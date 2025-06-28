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

### 実装の詳細解説

#### 1. ユーザー音声入力
- **実装場所**: `web-client/src/components/VoiceAssistant.tsx`
- **処理内容**: ブラウザのマイクAPIを使用して音声をキャプチャし、WebRTC経由でLiveKitサーバーに送信
- **関連コード**:
  ```javascript
  // VoiceAssistant.tsx内でLiveKitのuseVoiceAssistant hookを使用
  const { audioTrack } = useVoiceAssistant({ connectedRoomState });
  ```

#### 2. STT（音声→テキスト変換）
- **実装場所**: `agent-rag.py:144-148行目`
- **処理内容**: Azure OpenAIまたはOpenAIのWhisper APIを使用して音声をテキストに変換
- **関連コード**:
  ```python
  # Azure OpenAIを使用する場合
  stt=openai.STT.with_azure(model="gpt-4o-transcribe")
  # 通常のOpenAIを使用する場合
  stt=openai.STT(model="gpt-4o-transcribe")
  ```
- **音声処理フロー**: LiveKitのAgentクラス内部で自動的に処理される

#### 3. ChromaDBベクトル検索
- **実装場所**: `agent-rag.py:52-99行目` の `on_user_turn_completed` メソッド
- **処理タイミング**: ユーザーの発話が完了した時点で自動的に呼び出される
- **処理内容**:
  1. ユーザーの質問テキストをembeddingに変換（63-71行目）
  2. ChromaDBで類似度検索を実行（74-79行目）
  3. 検索結果をLLMのコンテキストに追加（82-90行目）
- **関連コード**:
  ```python
  async def on_user_turn_completed(self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage):
      # ユーザーの質問をembeddingに変換
      response = self.openai_client.embeddings.create(
          model=self.embedding_model,
          input=user_query
      )
      # ChromaDBで検索
      results = self.chroma_collection.query(
          query_embeddings=[query_embedding],
          n_results=3
      )
  ```

#### 4. 関連ドキュメント取得（上位3件）
- **実装場所**: `agent-rag.py:77行目`
- **処理内容**: `n_results=3` パラメータで上位3件の類似ドキュメントを取得
- **検索対象データ**: `test_data_extended.json` から生成されたembedding
- **データの準備**: `init_chromadb.py` で事前にベクトル化して保存

#### 5. LLM（GPT-4o-mini）で回答生成
- **実装場所**: `agent-rag.py:149行目, 156行目`
- **処理内容**: 検索結果を含めた拡張されたコンテキストでLLMが回答を生成
- **関連コード**:
  ```python
  # LLMの設定
  llm=openai.LLM.with_azure(model="gpt-4o-mini")  # Azureの場合
  llm=openai.LLM(model="gpt-4o-mini")  # 通常のOpenAIの場合
  
  # 検索結果がnew_message.contentに追加され、LLMに渡される
  enhanced_content = f"{context}\n\nユーザーの質問: {user_query}"
  new_message.content = enhanced_content
  ```

#### 6. TTS（テキスト→音声変換）
- **実装場所**: `agent-rag.py:150-154行目, 157-161行目`
- **処理内容**: LLMの回答テキストを音声に変換
- **関連コード**:
  ```python
  tts=openai.TTS.with_azure(
      model="gpt-4o-mini-tts",
      voice="ash",
      instructions="Speak in a friendly and conversational tone."
  )
  ```

#### 7. ユーザーへの音声応答
- **実装場所**: LiveKitの内部処理とWebクライアント
- **処理内容**: 生成された音声がWebRTC経由でブラウザに送信され、自動的に再生される

### データフローの詳細

1. **初期化時** (`initialize_chromadb_client` 関数):
   - ChromaDBクライアントを初期化
   - 既存のコレクションを読み込み
   - テストクエリで動作確認

2. **実行時**:
   - LiveKitが音声入力を自動的にSTTに渡す
   - `on_user_turn_completed`が呼び出される
   - ChromaDB検索が実行される
   - 検索結果がLLMのコンテキストに追加される
   - LiveKitが自動的にLLMとTTSを実行
   - 音声がクライアントに送信される

### デバッグ情報

実行時には以下のデバッグログが出力されます：
- `[DEBUG] on_user_turn_completed called with: <ユーザーの質問>`
- `[DEBUG] Creating embedding for query: <質問テキスト>`
- `[DEBUG] Search completed. Found X results`
- `[DEBUG] Result 1 (distance: X.XXXX): <ドキュメントの一部>...`

これらのログで検索が正しく動作しているか確認できます。

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

## よくある質問

### Q: なぜHTTPSでなくてもマイクが使えるのか？

ブラウザのセキュリティポリシーでは、通常`getUserMedia()` API（マイクやカメラへのアクセス）はセキュアコンテキスト（HTTPS）でのみ利用可能です。しかし、以下の例外があります：

1. **localhost例外**: `localhost`（127.0.0.1）は開発目的で特別扱いされ、HTTPでもセキュアコンテキストとして扱われます
   - `http://localhost:3000` ✅ 動作する
   - `http://192.168.1.100:3000` ❌ 動作しない（ローカルIPでもHTTPS必要）

2. **file://プロトコル**: ローカルファイルとして開いた場合も例外的に許可される場合があります

3. **ブラウザによる違い**:
   - Chrome/Edge: localhost例外を適用
   - Firefox: 同様にlocalhost例外を適用
   - Safari: より厳格な場合がある

### 本番環境での注意
- 本番環境では必ずHTTPSを使用してください
- Let's Encryptなどで無料のSSL証明書を取得可能
- 開発時はlocalhostを使用し、本番はHTTPSに切り替える

### Q: Webクライアントはどうやってマイクを認識・取得しているのか？

Webクライアントのマイクアクセスは、LiveKitのReactコンポーネントライブラリが自動的に処理します：

#### 1. **自動的なマイク有効化** (`App.tsx`)
```tsx
<LiveKitRoom
  audio={true}    // この設定でマイクが自動的に有効化される
  video={false}
  token={token}
  serverUrl={serverUrl}
>
```

#### 2. **内部的な処理フロー**
1. **接続時**: `LiveKitRoom`コンポーネントがマウント時に接続を開始
2. **権限リクエスト**: 内部で`navigator.mediaDevices.getUserMedia()`を呼び出し
3. **ブラウザプロンプト**: 初回はブラウザがマイク使用許可を求める
4. **音声トラック作成**: 許可後、`LocalAudioTrack`として音声ストリームを管理
5. **自動送信**: WebRTC経由でLiveKitサーバーに音声データを送信

#### 3. **ユーザーインターフェース** (`VoiceAssistant.tsx`)
```tsx
<ControlBar 
  controls={{
    microphone: true,    // マイクのON/OFFボタンを表示
  }}
/>
```
- ユーザーは画面下部のマイクボタンで手動でON/OFFを切り替え可能
- マイクの状態は視覚的にフィードバック（赤色=OFF、緑色=ON）

#### 4. **エラーハンドリング**
- マイクが見つからない場合: エラーメッセージを表示
- 権限が拒否された場合: 再度許可を求めるか、エラーを表示
- 複数のマイクがある場合: `MediaDeviceMenu`で選択可能

#### 5. **WSL2環境での動作**
WSL2はマイクデバイスに直接アクセスできませんが、Webクライアントは問題なく動作します：
- ブラウザ（Windows側）がマイクにアクセス
- 音声データはWebRTC経由でLiveKitサーバー（WSL2内）に送信
- Pythonエージェント（WSL2内）が音声を受信・処理