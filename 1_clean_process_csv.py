import csv
import os
import sys
import re

def extract_tracking_id(text):
    """件名からTrackingIDを抽出する関数"""
    # TrackingID#に続く数字を検索するパターン
    pattern = r"TrackingID#(\d+)"
    match = re.search(pattern, text)
    if match:
        return match.group(1)  # 数字部分だけを返す
    return None

def match_rate(str1, str2):
    # まずTrackingIDを抽出
    tracking_id1 = extract_tracking_id(str1)
    tracking_id2 = extract_tracking_id(str2)
    
    # 両方の文字列にTrackingIDが含まれており、それらが一致する場合
    if tracking_id1 and tracking_id2 and tracking_id1 == tracking_id2:
        return 100.0  # 100%一致とする
    
    # 以下は既存の一致度計算ロジック
    # 一致した文字数をカウントする変数を初期化する
    count = 0
    # 文字列1と文字列2の短い方の長さを取得する
    min_len = min(len(str1), len(str2))
    # 短い方の長さ分だけループする
    for i in range(min_len):
        # 文字列1と文字列2の末尾からi番目の文字が一致したら、カウントを増やす
        if str1[-(i+1)] == str2[-(i+1)]:
            count += 1
        # 一致しなかったら、ループを抜ける
        else:
            break
    # 一致度をパーセントで計算する（ゼロ除算を防止）
    rate = (count / min_len * 100) if min_len > 0 else 0
    # 一致度を返す
    return rate

def process_csv(input_file):
    # 入力ファイルのディレクトリを取得
    directory = os.path.dirname(input_file) if os.path.dirname(input_file) else '.'
    
    # 入力ファイル名から出力ファイル名を作成
    base_filename = os.path.basename(input_file)
    output_filename = f"cleaned_{base_filename}"
    output_file = os.path.join(directory, output_filename)
    
    print(f"処理結果は {output_file} に保存されます")
    
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
        
    # 件名カラムの存在チェック
    print(f"最初の行のデータ: {rows[0]}")
    
    # キーに「件名」を含むものを探す
    subject_key = None
    for key in rows[0].keys():
        # BOMと引用符を取り除いたキー名で比較
        clean_key = re.sub(r'[\ufeff"\']', '', key)
        if '件名' in clean_key:
            subject_key = key
            print(f"'件名'を含むカラムを見つけました: '{subject_key}'")
            break
    
    if not subject_key:
        print("CSVファイルに「件名」カラムがありません。処理を中止します。")
        return
        
    # 件名のリストを作成（BOMを考慮した件名キーを使用）
    subjects = [row[subject_key] for row in rows]
    
    # フィールド名のリストを作成（元のフィールド名 + Match_Rate + SR番号）
    original_fieldnames = list(rows[0].keys())
    fieldnames = original_fieldnames + ["Match_Rate", "SR番号"]
    
    # 各行に対して、前の行との一致度を計算する
    for i, row in enumerate(rows):
        current_subject = row[subject_key]
        # TrackingIDを抽出して「SR番号」として追加
        tracking_id_current = extract_tracking_id(current_subject)
        row["SR番号"] = tracking_id_current if tracking_id_current else ""
        
        # 最初の行以外に対して前の行との一致度を計算
        if i > 0:
            previous_subject = rows[i-1][subject_key]
            rate = match_rate(current_subject, previous_subject)
            
            # TrackingIDの情報をログに出力（デバッグ用）
            tracking_id_prev = extract_tracking_id(previous_subject)
            if tracking_id_current and tracking_id_prev:
                if tracking_id_current == tracking_id_prev:
                    print(f"TrackingID一致: {tracking_id_current} - Match率100%")
            
            # 一致度を格納
            row["Match_Rate"] = f"{rate:.2f}%"
            # 数値としても格納しておく（フィルタリング用）
            row["_match_rate_value"] = rate
        else:
            # 最初の行は前の行がないので、空または0%とする
            row["Match_Rate"] = "0.00%"
            row["_match_rate_value"] = 0
    
    # Match_Rateが80%以下の行だけをフィルタリング
    filtered_rows = [row for row in rows if row["_match_rate_value"] <= 80]
    
    # フィルタリング結果のログ出力
    print(f"全行数: {len(rows)}")
    print(f"Match_Rate 80%以下の行数: {len(filtered_rows)}")
    
    # 出力ファイルに書き込む
    try:
        # BOMありUTF-8で書き込み（Excel対応）- mode='w'で既存ファイルを上書き
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            # 一時フィールド(_match_rate_value)を除外したフィールド名リストを作成
            output_fieldnames = [field for field in fieldnames if field != "_match_rate_value"]
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            
            # 一時フィールドを削除してから書き込む
            for row in filtered_rows:
                # 一時フィールドをポップ（削除）
                if "_match_rate_value" in row:
                    row.pop("_match_rate_value")
                writer.writerow(row)
        
        print(f"処理が完了しました。結果は {output_file} に保存されました。")
        print(f"ファイルが既に存在していた場合は上書きされています。")
    except Exception as e:
        print(f"ファイル書き込み中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # コマンドライン引数からファイルパスを取得、なければデフォルトを使用
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # 絶対パスに修正
        input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "20250303_SR.CSV")
        print(f"入力ファイルが指定されていません。デフォルトファイル {input_file} を使用します。")
    
    # ファイルが存在するか確認
    if os.path.exists(input_file):
        process_csv(input_file)
    else:
        print(f"ファイル {input_file} が見つかりません。")
        print("使い方: python process_csv.py [CSVファイルのパス]")
        # ファイルが見つからない場合に詳細情報を表示
        print(f"現在の作業ディレクトリ: {os.getcwd()}")
        print(f"スクリプトの場所: {os.path.abspath(__file__)}")
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        print(f"推定されるdataディレクトリ: {data_dir}")
        if os.path.exists(data_dir):
            print(f"dataディレクトリが存在します。内容: {os.listdir(data_dir)}")
        else:
            print("dataディレクトリが存在しません。")