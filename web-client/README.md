# LiveKit Agent Web Client

WSL2環境での音声入出力問題を解決するためのWebベースのLiveKitエージェントクライアントです。

## セットアップ

1. 依存関係のインストール:
```bash
npm install
```

2. 開発サーバーの起動:
```bash
npm run dev
```

## 使用方法

1. まず、LiveKitエージェントを起動します:
```bash
cd ..
python agent.py dev
```

2. Webクライアントを開きます（自動的にブラウザが開きます）

3. "Connect to Agent"ボタンをクリックして接続します

4. マイクのアクセス許可を与えて、エージェントと会話を開始します

## 技術スタック

- React + TypeScript
- Vite
- LiveKit React SDK
- LiveKit Client SDK

## 開発用認証情報

開発環境では以下の認証情報を使用しています：
- API Key: `devkey`
- API Secret: `secret`
- LiveKit URL: `ws://localhost:7880`
