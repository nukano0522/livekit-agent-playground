# LiveKit Agent Playground

リアルタイム音声会話が可能なAIエージェントシステムです。ReactのWebクライアントとPythonのAIエージェントがLiveKitを介して通信します。

## システム構成

```
┌─────────────────┐     WebRTC/LiveKit      ┌──────────────────┐
│  Webクライアント  │ ◄─────────────────────► │  Python エージェント │
│   (React/TS)    │    ws://localhost:7880   │   (agent.py)      │
└─────────────────┘                          └──────────────────┘
        │                                             │
        │ 音声入出力                                   │ AI処理
        │                                             │
    🎤 マイク                                      📝 STT (音声認識)
    🔊 スピーカー                                  🤖 LLM (言語モデル)
                                                  🗣️ TTS (音声合成)
```

## 必要な環境

- Python 3.8以上
- Node.js 18以上
- LiveKitサーバー

### WSL2環境での注意事項
WSL2環境では直接音声入出力ができないため、付属のWebクライアントを使用してブラウザ経由で音声通信を行います。

## セットアップ

### 1. 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定してください：

```env
OPENAI_API_KEY=your-openai-api-key-here
LIVEKIT_API_KEY=devkey          # 開発環境のデフォルト値
LIVEKIT_API_SECRET=secret       # 開発環境のデフォルト値
LIVEKIT_URL=http://localhost:7880/
```

### 2. Pythonの依存関係インストール

```bash
# 仮想環境の作成（推奨）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install livekit-agents==1.1.3
pip install livekit-plugins-openai==1.1.3
pip install livekit-plugins-silero==1.1.3
pip install livekit-plugins-turn-detector==1.1.3
pip install livekit-plugins-noise-cancellation==0.2.4

# Ubuntu/Debian系での追加パッケージ（音声処理用）
sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-pyaudio
```

### 3. Webクライアントのセットアップ

```bash
cd web-client
npm install
```

## 実行方法

3つのコンポーネントを順番に起動します：

### 1. LiveKitサーバーの起動

[公式ドキュメント](https://docs.livekit.io/home/self-hosting/local/)に従ってセルフホストで実行します：

```bash
# LiveKitサーバーのインストール
curl -sSL https://get.livekit.io | bash

# 開発モードで起動
livekit-server --dev
```

これにより：
- LiveKitサーバーが自動的にダウンロード・インストールされます
- 開発モード（--dev）で起動し、以下のポートを使用します：
  - **ポート7880**: WebSocket接続用（クライアントとエージェントの通信）
  - **ポート7881**: Turn/STUN用（NAT越え）
  - **ポート7882/udp**: WebRTC メディア転送用
- 開発用の認証情報（API Key: "devkey", API Secret: "secret"）が自動設定されます

### 2. Pythonエージェントの起動

```bash
# プロジェクトルートで
python agent.py dev
```

このコマンドは以下を実行します：
- LiveKitエージェントフレームワークの初期化
- OpenAI APIとの接続設定
- 音声処理パイプラインの構築（VAD、STT、LLM、TTS）
- WebSocketでLiveKitサーバーに接続し、音声セッションを待機

### 3. Webクライアントの起動

```bash
cd web-client
npm run dev
```

このコマンドは以下を実行します：
- Vite開発サーバーをポート3000で起動
- 自動的にブラウザでhttp://localhost:3000を開く
- ホットリロード対応の開発環境を提供

## 使用方法

1. ブラウザで http://localhost:3000 にアクセス（自動的に開きます）
2. 「Connect to Agent」ボタンをクリック
3. ブラウザのマイクアクセスを許可
4. 音声で話しかけるとAIアシスタントが応答します

## アーキテクチャ詳細

### 通信フローの仕組み

1. **LiveKitサーバーの役割**
   - WebRTC通信の仲介
   - ルーム（通信空間）の管理
   - 参加者間の音声ストリーム中継

2. **Webクライアント側の処理**
   ```typescript
   // 1. 接続時に新しいルーム名を生成
   const roomName = `agent-room-${Date.now()}`
   
   // 2. JWTトークンで認証
   const token = await generateToken(roomName, participantName)
   
   // 3. LiveKitルームに接続
   <LiveKitRoom token={token} serverUrl="ws://localhost:7880">
     <VoiceAssistant />
   </LiveKitRoom>
   ```

3. **Pythonエージェント側の処理**
   ```python
   # エージェントセッションの設定
   session = AgentSession(
       stt=openai.STT(),      # 音声→テキスト
       llm=openai.LLM(),      # AI応答生成
       tts=openai.TTS(),      # テキスト→音声
       vad=silero.VAD(),      # 音声検出
   )
   
   # ルームへの自動参加と応答生成
   await session.start(room, agent)
   ```

### 音声処理フロー

```
ユーザー音声入力
    ↓
Webクライアント（マイク録音）
    ↓
LiveKitサーバー（WebRTC転送）
    ↓
Pythonエージェント
    ├─ STT: 音声をテキストに変換
    ├─ LLM: AIが応答を生成
    └─ TTS: 応答を音声に変換
    ↓
LiveKitサーバー（WebRTC転送）
    ↓
Webクライアント（スピーカー再生）
```

### コンポーネント詳細

#### Pythonエージェント（agent.py）
- **Assistant クラス**: LiveKitのAgentベースクラスを拡張
- **音声処理パイプライン**:
  - Silero VAD: 音声アクティビティ検出
  - OpenAI Whisper: 音声認識（STT）
  - OpenAI GPT-4o-mini: 言語処理（LLM）
  - OpenAI TTS: 音声合成

#### Webクライアント（web-client/）
- **React + TypeScript + Vite**: モダンなフロントエンド構成
- **LiveKit Client SDK**: WebRTC通信の管理
- **主要コンポーネント**:
  - App.tsx: メインアプリケーション（接続管理）
  - TokenGenerator: JWT認証トークンの生成
  - VoiceAssistant: 音声対話UI
  - RoomAudioRenderer: 音声の送受信管理

## トラブルシューティング

### エージェントが起動しない
- `.env`ファイルが正しく設定されているか確認
- LiveKitサーバーが起動しているか確認（http://localhost:7880 でアクセス可能か）
- Pythonの依存関係が全てインストールされているか確認

### 音声が認識されない
- ブラウザのマイクアクセスが許可されているか確認
- マイクが正しく選択されているか確認
- ブラウザのコンソールでエラーが出ていないか確認

### WSL2での問題
- 必ずWebクライアント経由で接続する（`python agent.py dev`だけでは音声入出力不可）
- Windowsファイアウォールがポート3000と7880-7882を許可しているか確認

## 開発のヒント

- エージェントの挙動を変更する場合は`agent.py`の`Assistant`クラスを編集
- UIを変更する場合は`web-client/src/`内のReactコンポーネントを編集
- 新しいLLMプロンプトやインストラクションは`agent.py`の`entrypoint`関数内で設定