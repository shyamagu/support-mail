import csv
import os
import sys
import re
import json
from openai_utils import SupportCategory, call_openai_completion

# カテゴリのリストを定義
USER_REQUEST_CATEGORIES = [
    "specConfirmation",
    "maintenanceIssue",
    "productFailure",
    "quotaManagement",
    "billingIssue",
    "thirdPartyProductIssue",
    "other"
]

SUPPORT_RESPONSE_CATEGORIES = [
    "providedPublicDocs",
    "explainedWithoutPublicDocs",
    "analyzedLogs",
    "reportedProductFailure",
    "supportedByOverseasTeam",
    "quotaManagement",
    "billingIssue",
    "other"
]

def process_csv(input_file):
    # CSVファイルを読み込む
    try:
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except UnicodeDecodeError:
        # UTF-8で開けない場合はCP932(Shift-JIS)で試行
        with open(input_file, 'r', encoding='cp932') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
    if not rows:
        print("CSVファイルにデータがありませんでした。")
        return
        
    # 件名と本文カラムの存在チェック
    print(f"最初の行のデータ: {rows[0]}")
    
    # キーに「件名」と「本文」を含むものを探す
    subject_key = None
    body_key = None
    sr_number_key = "SR番号"  # SR番号のカラム名
    
    for key in rows[0].keys():
        # BOMと引用符を取り除いたキー名で比較
        clean_key = re.sub(r'[\ufeff"\']', '', key)
        if '件名' in clean_key:
            subject_key = key
            print(f"'件名'を含むカラムを見つけました: '{subject_key}'")
        elif '本文' in clean_key:
            body_key = key
            print(f"'本文'を含むカラムを見つけました: '{body_key}'")
        
        if subject_key and body_key:
            break
    
    if not subject_key:
        print("CSVファイルに「件名」カラムがありません。処理を中止します。")
        return

    if not body_key:
        print("CSVファイルに「本文」カラムがありません。処理を中止します。")
        return
    
    # SR番号カラムの存在チェック
    sr_number_exists = sr_number_key in rows[0]
    if not sr_number_exists:
        print(f"警告: CSVファイルに「{sr_number_key}」カラムがありません。重複チェックは件名のみで行います。")
    
    # 出力ファイル名を設定
    input_filename = os.path.basename(input_file)
    output_filepath = os.path.join(os.path.dirname(input_file), f"analyzed_{input_filename}")
    print(f"解析結果は {output_filepath} に保存されます")

    # 出力用のフィールド名を設定
    output_fieldnames = []
    if sr_number_exists:
        output_fieldnames.append(sr_number_key)
    output_fieldnames.append(subject_key)  # 件名
    output_fieldnames.extend(["closed", "bug", "user_request_category", "support_team_response_category"])
    
    # マトリクス形式のカテゴリ列を追加
    # 問い合わせカテゴリのマトリクス列
    for category in USER_REQUEST_CATEGORIES:
        output_fieldnames.append(f"user_{category}")
    
    # 回答カテゴリのマトリクス列
    for category in SUPPORT_RESPONSE_CATEGORIES:
        output_fieldnames.append(f"css_{category}")
    
    # 解析結果の格納用
    analyzed_rows = []
    
    # 既に処理済みのSR番号を記録するセット
    processed_sr_numbers = set()
    
    # 各行を処理
    total_rows = len(rows)
    skipped_rows = 0
    
    for i, row in enumerate(rows, 1):
        # SR番号の重複チェック
        sr_number = row.get(sr_number_key, "") if sr_number_exists else ""
        
        # SR番号が存在し、すでに処理済みの場合はスキップ
        if sr_number and sr_number in processed_sr_numbers:
            print(f"スキップ... {i}/{total_rows}: SR番号 {sr_number} は重複しています。")
            skipped_rows += 1
            continue
        
        print(f"処理中... {i}/{total_rows}: {row[subject_key][:30]}...")
        
        # 新しい行データを作成（必要な列のみ含む）
        new_row = {}
        if sr_number_exists:
            new_row[sr_number_key] = sr_number
            # 空でないSR番号を処理済みとして記録
            if sr_number:
                processed_sr_numbers.add(sr_number)
        new_row[subject_key] = row[subject_key]
        
        # 本文があれば解析する
        if body_key and row[body_key]:
            body = row[body_key]
            try:
                # OpenAI APIを呼び出して解析
                support_category = call_openai_completion(body, SupportCategory)
                
                # 結果をCSV用に整形
                new_row["closed"] = getattr(support_category, "closed", "")  # closedフィールドがあれば取得、なければ空文字
                new_row["bug"] = support_category.bug
                new_row["user_request_category"] = ", ".join(support_category.user_request_category)
                new_row["support_team_response_category"] = ", ".join(support_category.support_team_response_category)
                
                # マトリクス形式のカテゴリデータを追加
                # 問い合わせカテゴリの0,1マトリクス
                for category in USER_REQUEST_CATEGORIES:
                    new_row[f"user_{category}"] = 1 if category in support_category.user_request_category else 0
                
                # 回答カテゴリの0,1マトリクス
                for category in SUPPORT_RESPONSE_CATEGORIES:
                    new_row[f"css_{category}"] = 1 if category in support_category.support_team_response_category else 0
                
                print(f"  解析完了: bug={support_category.bug}, closed={getattr(support_category, 'closed', '')}")
            except Exception as e:
                print(f"  エラー発生: {str(e)}")
                new_row["closed"] = ""
                new_row["bug"] = ""
                new_row["user_request_category"] = ""
                new_row["support_team_response_category"] = ""
                
                # エラーの場合は、マトリクス列をすべて0に設定
                for category in USER_REQUEST_CATEGORIES:
                    new_row[f"user_{category}"] = 0
                for category in SUPPORT_RESPONSE_CATEGORIES:
                    new_row[f"css_{category}"] = 0
        else:
            # 本文がない場合は空欄に
            new_row["closed"] = ""
            new_row["bug"] = ""
            new_row["user_request_category"] = ""
            new_row["support_team_response_category"] = ""
            
            # 本文がない場合も、マトリクス列をすべて0に設定
            for category in USER_REQUEST_CATEGORIES:
                new_row[f"user_{category}"] = 0
            for category in SUPPORT_RESPONSE_CATEGORIES:
                new_row[f"css_{category}"] = 0
        
        analyzed_rows.append(new_row)

    # フィルタリング結果のログ出力
    print(f"\n全行数: {total_rows}")
    print(f"重複により除外された行数: {skipped_rows}")
    print(f"処理された行数: {len(analyzed_rows)}")

    # CSVファイルに結果を書き込む
    try:
        with open(output_filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            for row in analyzed_rows:
                writer.writerow(row)
        print(f"\n解析が完了しました。結果は {output_filepath} に保存されました。")
    except Exception as e:
        print(f"ファイル書き込み中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # コマンドライン引数からファイルパスを取得
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        
        # ファイルが存在するか確認
        if os.path.exists(input_file):
            process_csv(input_file)
        else:
            print(f"\nエラー: ファイル {input_file} が見つかりません。")
            print("\nファイルパスを指定して再度実行してください:")
            print("python 2_analyze_process_csv.py [CSVファイルのパス]")
            print("\n例: python 2_analyze_process_csv.py cleaned_sample.CSV")
            print("\n注意: このスクリプトは1_clean_process_csv.pyで処理された「cleaned_」から始まるCSVファイルを入力として想定しています。")
    else:
        print("\nエラー: 入力ファイルが指定されていません。")
        print("\nファイルパスを指定して実行してください:")
        print("python 2_analyze_process_csv.py [CSVファイルのパス]")
        print("\n例: python 2_analyze_process_csv.py cleaned_sample.CSV")
        print("\n注意: このスクリプトは1_clean_process_csv.pyで処理された「cleaned_」から始まるCSVファイルを入力として想定しています。")