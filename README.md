# CSS_SR データ処理・分析ツール

## 概要
このプロジェクトは、マイクロソフトのサポートチーム(CSS)と顧客とのメールスレッドを含むCSVファイルを処理し、OpenAI APIを使って分析するツールです。プロセスは2つの主要なステップで構成されています：

1. CSVデータのクリーニングと重複除去（`1_clean_process_csv.py`）
2. OpenAI APIを使用したデータ分析（`2_analyze_process_csv.py`）

## 必要条件
- Python 3.9以上
- 以下のPythonパッケージ：
  - pydantic
  - openai
  - python-dotenv

## インストール方法

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/CSS_SR.git
cd CSS_SR
```

### 2. 仮想環境の作成と有効化（推奨）
```bash
# Windowsの場合
python -m venv venv
venv\Scripts\activate

# macOS/Linuxの場合
python -m venv venv
source venv/bin/activate
```

### 3. 依存パッケージのインストール
```bash
pip install -r requirements.in
```

### 4. 環境変数の設定
プロジェクトのルートディレクトリに `.env` ファイルを作成し、以下の内容を設定してください：

```
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
MODEL_DEPLOYMENT_NAME=your_model_deployment_name
```

## 使用方法

### ステップ1: CSVデータのクリーニング
このスクリプトは、入力CSVファイルを処理し、重複を取り除き、TrackingIDを抽出します。また、件名の一致率が80%以下の行のみをフィルタリングします。

```bash
python 1_clean_process_csv.py [CSVファイルのパス]
```

例：
```bash
python 1_clean_process_csv.py data/20250303_SR.CSV
```

処理結果は入力ファイルと同じディレクトリに `cleaned_[元のファイル名].CSV` として保存されます。

### ステップ2: データ分析
このスクリプトは、ステップ1でクリーニングされたCSVファイルを読み込み、OpenAI APIを使用して各サポートケースを分析します。

```bash
python 2_analyze_process_csv.py [クリーニング済みCSVファイルのパス]
```

例：
```bash
python 2_analyze_process_csv.py data/cleaned_20250303_SR.CSV
```

分析結果は入力ファイルと同じディレクトリに `analyzed_[元のファイル名].CSV` として保存されます。

## 分析結果について
分析では以下の情報が抽出されます：

- ケースがクローズされているかどうか（1 or 0）
- Microsoftの製品の不具合に起因する問題かどうか（1 or 0）
- ユーザーリクエストのカテゴリ（複数可）
- サポートチームの対応カテゴリ（複数可）

## トラブルシューティング

### ファイルが見つからない場合
ファイルパスを正確に指定しているか確認してください。相対パスで指定する場合は、スクリプトを実行しているディレクトリからの相対パスとなります。

### 文字化けが発生する場合
CSVファイルは UTF-8 または Shift-JIS (CP932) でエンコードされていることを前提としています。他のエンコーディングの場合は、スクリプトを適宜修正してください。

### API接続の問題
`.env` ファイルの設定が正しいか確認し、ネットワーク接続に問題がないことを確認してください。