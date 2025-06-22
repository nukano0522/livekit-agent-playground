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

# 2. Pythonエージェント
python agent.py dev

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

## Architecture

### 通信フロー
1. Webクライアント（React）がブラウザのマイクから音声入力を取得
2. LiveKitサーバー（ws://localhost:7880）経由でPythonエージェントに転送
3. Pythonエージェントが音声処理パイプラインで応答生成：
   - STT (OpenAI Whisper): 音声→テキスト
   - LLM (GPT-4o-mini): AI応答生成
   - TTS (OpenAI): テキスト→音声
4. 生成された音声をWebクライアントで再生

### 主要ファイル
- `agent.py`: メインエージェント実装（Assistant class）
- `agent-rag.py`: RAG対応の別実装
- `web-client/src/App.tsx`: クライアントのメインコンポーネント
- `web-client/src/components/TokenGenerator.tsx`: JWT認証トークン生成
- `web-client/src/components/VoiceAssistant.tsx`: 音声対話UI

### ポート使用
- 3000: Webクライアント（Vite開発サーバー）
- 7880: LiveKit WebSocket
- 7881: Turn/STUN
- 7882/udp: WebRTC メディア転送

## Known Issues

1. **WSL2環境**: 直接音声入出力ができないため、必ずWebクライアント経由で使用
2. **テストの欠如**: 現在、Python/JavaScript両方でテストが実装されていない
3. **CI/CD未設定**: 自動ビルド・デプロイの仕組みがない