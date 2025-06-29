# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

日本語で応答してください。

## Project Overview

LiveKit音声AIエージェントのプレイグラウンド。WebクライアントとPythonエージェントがLiveKit経由でリアルタイム音声通信を実現します。3つの異なるエージェント実装（基本、RAG、プロキシ）を含み、WSL2環境でも動作可能。

## Key Dependencies

### Python
- `livekit-agents[deepgram,openai,cartesia,silero,turn-detector]~=1.0`
- `livekit-plugins-noise-cancellation~=0.2`
- `chromadb==1.0.13` (RAG実装用)
- `python-dotenv`

注意: README.mdには具体的なバージョン（1.1.3）が記載されているが、requirements.txtは柔軟なバージョン指定を使用

### JavaScript/TypeScript (web-client)
- React 19.1.0
- TypeScript 5.8.3
- Vite 6.3.5
- @livekit/components-react, livekit-client, livekit-server-sdk

## Common Commands

### 開発環境の起動（3つのコンポーネントを順番に）

```bash
# 1. LiveKitサーバー
curl -sSL https://get.livekit.io | bash  # 初回のみ
livekit-server --dev

# 2. Pythonエージェント（3種類から選択）
python agent.py dev          # 基本エージェント
python agent-rag.py dev      # RAG対応エージェント（ChromaDB使用）
python agent-proxy.py        # プロキシエージェント

# 3. Webクライアント
cd web-client
npm run dev
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
# Python
pip install -r requirements.txt

# Ubuntu/Debian系での音声処理用パッケージ
sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-pyaudio

# JavaScript
cd web-client && npm install
```

### RAG実装の初期化

```bash
# ChromaDBの初期化（RAG使用時に必要）
python init_chromadb.py
```

### 開発用ユーティリティ

```bash
# 音声デバイスの確認（トラブルシューティング用）
python check_audio_devices.py
```

## Architecture

### エージェント実装の種類
1. **agent.py**: 基本的な音声対話エージェント（OpenAI Whisper + GPT-4o-mini + TTS）
2. **agent-rag.py**: ChromaDBを使用したRAG（Retrieval-Augmented Generation）対応版
3. **agent-proxy.py**: プロキシモードのエージェント実装

### 通信フロー
1. Webクライアント（React）がブラウザのマイクから音声入力を取得
2. LiveKitサーバー（ws://localhost:7880）経由でPythonエージェントに転送
3. Pythonエージェントが音声処理パイプラインで応答生成：
   - STT (OpenAI Whisper): 音声→テキスト
   - LLM (GPT-4o-mini): AI応答生成（RAG版はChromaDBから関連情報取得）
   - TTS (OpenAI): テキスト→音声
4. 生成された音声をWebクライアントで再生

### 主要ファイル
- `agent.py`: メインエージェント実装（Assistant class）
- `agent-rag.py`: RAG対応の別実装（ChromaDB統合）
- `init_chromadb.py`: ChromaDBの初期データ投入スクリプト
- `test_data.json`, `test_data_extended.json`: RAG用のサンプルデータ
- `web-client/src/App.tsx`: クライアントのメインコンポーネント
- `web-client/src/components/TokenGenerator.tsx`: JWT認証トークン生成
- `web-client/src/components/VoiceAssistant.tsx`: 音声対話UI

### ポート使用
- 3000: Webクライアント（Vite開発サーバー）
- 7880: LiveKit WebSocket
- 7881: Turn/STUN
- 7882/udp: WebRTC メディア転送

### 環境変数設定
`.env`ファイルを作成し、以下の変数を設定：
```
OPENAI_API_KEY=your_openai_api_key
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_URL=ws://localhost:7880
```

Azure OpenAI使用時は追加で：
```
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_KEY=your_azure_key
```

## Known Issues

1. **WSL2環境**: 直接音声入出力ができないため、必ずWebクライアント経由で使用
2. **テストの欠如**: 現在、Python/JavaScript両方でテストが実装されていない
3. **CI/CD未設定**: 自動ビルド・デプロイの仕組みがない
4. **ChromaDB初期化**: RAG版使用時は事前に`init_chromadb.py`の実行が必要