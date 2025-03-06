import csv
import os
import sys
import re

def extract_data_for_check(input_file):
    """
    CSVファイルを読み込み、件名とSR番号のみを抽出したCSVファイルを作成します
    出力ファイル名は 'forcheck_元のファイル名' となります
    """
    # 入力ファイルのディレクトリを取得
    directory = os.path.dirname(input_file) if os.path.dirname(input_file) else '.'
    
    # 入力ファイル名から出力ファイル名を作成
    base_filename = os.path.basename(input_file)
    output_filename = f"forcheck_{base_filename}"
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
    sr_number_key = "SR番号"  # SR番号のカラム名
    
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
    
    # SR番号カラムの存在チェック
    sr_number_exists = sr_number_key in rows[0]
    if not sr_number_exists:
        print(f"警告: CSVファイルに「{sr_number_key}」カラムがありません。")
    
    # 出力用のフィールド名を設定（件名とSR番号のみ）
    output_fieldnames = [subject_key]
    if sr_number_exists:
        output_fieldnames.append(sr_number_key)
        
    # 出力用の行データを作成（件名とSR番号のみ含む）
    output_rows = []
    for row in rows:
        new_row = {subject_key: row[subject_key]}
        if sr_number_exists:
            new_row[sr_number_key] = row[sr_number_key]
        output_rows.append(new_row)
    
    # CSVファイルに結果を書き込む
    try:
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            for row in output_rows:
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
        input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cleaned_20250303_SR.CSV")
        print(f"入力ファイルが指定されていません。デフォルトファイル {input_file} を使用します。")
    
    # ファイルが存在するか確認
    if os.path.exists(input_file):
        extract_data_for_check(input_file)
    else:
        print(f"ファイル {input_file} が見つかりません。")
        print("使い方: python check_simple_csv.py [CSVファイルのパス]")
        # ファイルが見つからない場合に詳細情報を表示
        print(f"現在の作業ディレクトリ: {os.getcwd()}")
        print(f"スクリプトの場所: {os.path.abspath(__file__)}")
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        print(f"推定されるdataディレクトリ: {data_dir}")
        if os.path.exists(data_dir):
            print(f"dataディレクトリが存在します。内容: {os.listdir(data_dir)}")
        else:
            print("dataディレクトリが存在しません。")