import sys
import os.path
import csv

def main():
    # コマンドライン引数をチェック
    if len(sys.argv) != 2:
        print("使用方法: python y_top10_export_csv.py [csvファイル名]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # ファイルが存在するか確認
    if not os.path.exists(input_file):
        print(f"エラー: ファイル '{input_file}' が見つかりません。")
        sys.exit(1)
    
    try:
        # 出力ファイル名を生成
        basename = os.path.basename(input_file)
        output_file = os.path.join(os.path.dirname(input_file), "top10_" + basename)
        
        # エンコーディングを試行（UTF-8とCP932）
        rows = []
        fieldnames = []
        
        try:
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                # 上位10件のデータのみ取得
                for i, row in enumerate(reader):
                    if i < 10:  # 10行だけ取得
                        rows.append(row)
                    else:
                        break
        except UnicodeDecodeError:
            # UTF-8で開けない場合はCP932(Shift-JIS)で試行
            with open(input_file, 'r', encoding='cp932') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                # 上位10件のデータのみ取得
                for i, row in enumerate(reader):
                    if i < 10:  # 10行だけ取得
                        rows.append(row)
                    else:
                        break
        
        # データが存在するか確認
        if not rows:
            print("CSVファイルにデータがありませんでした。")
            sys.exit(1)
        
        # 新しいCSVファイルに保存
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"成功: 上位10件のデータを '{output_file}' に保存しました。")
    
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
