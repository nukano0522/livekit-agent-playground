# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

日本語で応答してください。

## Project Overview

LiveKit音声AIエージェントのプレイグラウンド。WebクライアントとPythonエージェントがLiveKit経由でリアルタイム音声通信を実現します。WSL2環境でも動作可能。

## Key Dependencies

### Python
- `livekit-agents[deepgram,openai,cartesia,silero,turn-detector]~=1.0`
- `livekit-plugins-noise-cancellation~=0.2`
- `python-dotenv`
- `chromadb==1.0.13` (RAG機能用)

注意: README.mdには具体的なバージョン（1.1.3）が記載されているが、requirements.txtは柔軟なバージョン指定を使用

### JavaScript/TypeScript (web-client)
- React 19.1.0
- TypeScript 5.8.3
- Vite 6.3.5
- @livekit/components-react ^2.9.10
- livekit-client ^2.13.8
- livekit-server-sdk ^2.13.0

## Environment Variables

### 基本設定（.env）
```env
# OpenAI API（通常版）
OPENAI_API_KEY=your-openai-api-key

# Azure OpenAI（企業向け）
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Azure OpenAI Embedding専用（RAG用）
AZURE_OPENAI_ENDPOINT_EM=https://your-embedding-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY_EM=your-embedding-api-key
OPENAI_API_VERSION_EM=2024-08-01-preview
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# LiveKit設定（開発環境のデフォルト）
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_URL=http://localhost:7880/

# プロキシ設定（必要な場合）
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
```

## Common Commands

### 開発環境の起動（3つのコンポーネントを順番に）

```bash
# 1. LiveKitサーバー
curl -sSL https://get.livekit.io | bash  # 初回のみ
livekit-server --dev

# 2. Pythonエージェント
python agent.py dev        # 通常版
python agent-rag.py dev    # RAG対応版
python agent-proxy.py dev  # プロキシ対応版

# 3. Webクライアント
cd web-client
npm run dev
```

### RAG機能の初期化

```bash
# ChromaDBの初期化とサンプルデータの登録
python init_chromadb.py
```

### Webクライアントのコマンド

```bash
cd web-client
npm run lint     # ESLintでコードチェック
npm run build    # プロダクションビルド
npm run preview  # ビルド後のプレビュー
```

### 依存関係のインストール

```bash
# Python仮想環境の作成（推奨）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Python依存関係
pip install -r requirements.txt

# Ubuntu/Debian系での音声処理用パッケージ
sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-pyaudio

# JavaScript依存関係
cd web-client && npm install
```

## Architecture

### 通信フロー
1. Webクライアント（React）がブラウザのマイクから音声入力を取得
2. LiveKitサーバー（ws://localhost:7880）経由でPythonエージェントに転送
3. Pythonエージェントが音声処理パイプラインで応答生成：
   - VAD (Silero): 音声アクティビティ検出
   - STT (OpenAI Whisper/gpt-4o-transcribe): 音声→テキスト
   - LLM (GPT-4o-mini): AI応答生成
   - TTS (OpenAI/gpt-4o-mini-tts): テキスト→音声
4. 生成された音声をWebクライアントで再生

### 主要ファイル

#### Pythonエージェント
- `agent.py`: メインエージェント実装（Assistant class）
- `agent-rag.py`: ChromaDB RAG対応版（ベクトル検索機能付き）
- `agent-proxy.py`: プロキシ環境対応版
- `init_chromadb.py`: RAG用データベース初期化スクリプト

#### Webクライアント
- `web-client/src/App.tsx`: メインアプリケーション（接続管理）
- `web-client/src/components/TokenGenerator.tsx`: JWT認証トークン生成
- `web-client/src/components/VoiceAssistant.tsx`: 音声対話UI
- `web-client/src/components/RoomAudioRenderer.tsx`: 音声送受信管理

#### データファイル
- `test_data_extended.json`: RAG用サンプルデータ（LiveKit社の情報）
- `chroma_db/`: ChromaDBのデータベースファイル

### ポート使用
- 3000: Webクライアント（Vite開発サーバー）
- 7880: LiveKit WebSocket
- 7881: Turn/STUN
- 7882/udp: WebRTC メディア転送

## エージェントのバリエーション

### 1. 通常版 (agent.py)
- 基本的な音声対話機能
- OpenAIまたはAzure OpenAI対応
- シンプルな実装で理解しやすい

### 2. RAG対応版 (agent-rag.py)
- ChromaDBを使用したベクトル検索機能
- `on_user_turn_completed`メソッドで検索実行
- 検索結果をLLMのコンテキストに追加
- 企業情報などの固定データに基づく応答が可能

### 3. プロキシ対応版 (agent-proxy.py)
- 企業プロキシ環境での動作に対応
- HTTP_PROXY/HTTPS_PROXY環境変数を使用
- urllib3のプロキシ設定を自動構成

## Known Issues

1. **WSL2環境**: 直接音声入出力ができないため、必ずWebクライアント経由で使用
2. **テストの欠如**: 現在、Python/JavaScript両方でテストが実装されていない
3. **CI/CD未設定**: 自動ビルド・デプロイの仕組みがない
4. **ChromaDB永続化**: SQLiteファイルがGitで追跡されている（本番では要改善）

## 開発のヒント

1. **デバッグログ**: RAG版では`[DEBUG]`プレフィックスで検索状況を出力
2. **音声認識の精度**: マイクの品質と環境ノイズが大きく影響
3. **レスポンス速度**: Azure OpenAIの方が一般的に高速
4. **カスタマイズ**: `Assistant`クラスの`entrypoint`関数でプロンプトを調整

## トラブルシューティング

### よくある問題
- **マイクアクセス**: ブラウザの権限設定を確認（localhost例外により、HTTPでも動作）
- **ポート競合**: 他のサービスが7880-7882を使用していないか確認
- **API認証**: 環境変数が正しく設定されているか確認（.envファイル）
- **ChromaDBエラー**: `init_chromadb.py`を再実行してデータベースを初期化

## Important Instruction Reminders

- 必要な場合にのみファイルを作成する
- 既存ファイルの編集を新規作成より優先する
- プロアクティブにドキュメントファイル（*.md）を作成しない