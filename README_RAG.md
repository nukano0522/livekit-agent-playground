# ChromaDB RAGシステム セットアップガイド

## 概要
このドキュメントでは、LiveKitエージェントにChromaDBを使用したRAG（Retrieval-Augmented Generation）システムの実装について説明します。

## セットアップ手順

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定
`.env`ファイルに以下の環境変数を設定してください：

#### Azure OpenAIを使用する場合（推奨）
```env
# STT/TTS/LLM用のエンドポイント
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Embedding専用のエンドポイント
AZURE_OPENAI_ENDPOINT_EM=https://di-poc2.openai.azure.com/
AZURE_OPENAI_API_KEY_EM=your-embedding-api-key-here
OPENAI_API_VERSION_EM=2024-08-01-preview
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

#### 通常のOpenAIを使用する場合
```env
OPENAI_API_KEY=your-openai-api-key
```

### 3. ChromaDBの初期化とデータ登録
```bash
python init_chromadb.py
```

このコマンドで以下が実行されます：
- ChromaDBコレクションの作成
- サンプルデータ（test_data_extended.json）の読み込み
- 各ドキュメントのembedding生成
- ChromaDBへのデータ登録

### 4. LiveKitサーバーの起動
```bash
livekit-server --dev
```

### 5. RAGエージェントの起動
```bash
python agent-rag.py dev
```

### 6. Webクライアントの起動
```bash
cd web-client
npm install  # 初回のみ
npm run dev
```

## 使い方

1. ブラウザで `http://localhost:3000` にアクセス
2. マイクボタンをクリックして音声入力を開始
3. LiveKit株式会社に関する質問をする

### 質問例
- "LiveKit Cloudの価格を教えてください"
- "どんなAIモデルに対応していますか？"
- "医療業界での導入事例はありますか？"
- "技術仕様について教えてください"
- "エンタープライズサポートの内容は？"

## システムアーキテクチャ

```
ユーザー音声入力
    ↓
STT（音声→テキスト変換）
    ↓
ChromaDBベクトル検索
    ↓
関連ドキュメント取得（上位3件）
    ↓
LLM（GPT-4o-mini）で回答生成
    ↓
TTS（テキスト→音声変換）
    ↓
ユーザーへの音声応答
```

## トラブルシューティング

### ChromaDB関連のエラー
- `init_chromadb.py`を再実行してデータベースを初期化
- `./chroma_db`ディレクトリを削除して再作成

### Embeddingエラー
- Azure OpenAIのAPIキーとエンドポイントが正しく設定されているか確認
- `AZURE_OPENAI_EMBEDDING_MODEL`が正しいデプロイメント名になっているか確認

### 音声認識がうまくいかない場合
- ブラウザのマイク権限を確認
- ChromeまたはEdgeの最新版を使用

## カスタマイズ

### データの追加・更新
1. `test_data_extended.json`を編集
2. `python init_chromadb.py`を実行してデータベースを更新

### 検索精度の調整
`agent-rag.py`の`n_results=3`を変更して検索結果の数を調整できます。

## 注意事項
- WSL2環境では直接音声入出力ができないため、必ずWebクライアント経由で使用してください
- 初回実行時はembedding生成に時間がかかる場合があります