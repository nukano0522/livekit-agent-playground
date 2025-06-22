# 外部システム連携実装計画

## 概要
LiveKit AgentでSTT（音声認識）の結果を基に、外部システムと連携してRAG検索や外部API実行を行い、その結果をLLMに渡して応答を生成する機能の実装計画。

## 実装予定の機能

### 1. 基本アーキテクチャの拡張

#### 1.1 Assistantクラスのカスタマイズ
```python
class Assistant(Agent):
    async def on_user_speech_committed(self, message: str):
        """ユーザーの発話がSTTで確定したタイミングで呼ばれる"""
        # 1. 外部APIを呼び出し
        external_data = await self.call_external_api(message)
        
        # 2. RAG検索を実行
        rag_results = await self.search_knowledge_base(message)
        
        # 3. LLMのコンテキストに追加
        self.chat_context.add_message(
            role="system",
            content=f"関連情報: {external_data}\n検索結果: {rag_results}"
        )
```

#### 1.2 処理フローの設計
```
ユーザー音声入力
    ↓
STT（音声認識）
    ↓
┌─────────────────────┐
│  カスタム処理レイヤー  │
├─────────────────────┤
│ • 外部API呼び出し    │
│ • RAG検索           │
│ • データ前処理       │
└─────────────────────┘
    ↓
LLM（コンテキスト付き）
    ↓
TTS（音声合成）
    ↓
ユーザーへの応答
```

### 2. RAG（Retrieval-Augmented Generation）実装

#### 2.1 ベクトルデータベース統合
- [ ] ベクトルDB選定（Pinecone, Weaviate, ChromaDB等）
- [ ] 埋め込みモデルの実装（OpenAI Embeddings）
- [ ] 類似度検索機能の実装
- [ ] インデックス管理機能

#### 2.2 知識ベース管理
```python
class KnowledgeBaseManager:
    async def index_documents(self, documents: List[Document]):
        """ドキュメントをベクトル化してインデックス"""
        pass
    
    async def search(self, query: str, top_k: int = 5) -> List[Document]:
        """クエリに関連するドキュメントを検索"""
        pass
    
    async def update_index(self, doc_id: str, new_content: str):
        """既存ドキュメントの更新"""
        pass
```

### 3. 外部API連携

#### 3.1 API統合パターン
- [ ] REST API クライアントの実装
- [ ] GraphQL クライアントの実装
- [ ] WebSocket接続によるリアルタイムデータ取得
- [ ] 認証機構の実装（OAuth2, API Key等）

#### 3.2 具体的な連携例
```python
class ExternalAPIManager:
    async def weather_api(self, location: str):
        """天気情報API連携"""
        pass
    
    async def database_query(self, sql: str):
        """データベース検索"""
        pass
    
    async def third_party_service(self, params: dict):
        """サードパーティサービス連携"""
        pass
```

### 4. LLMツール機能の活用

#### 4.1 Function Calling実装
```python
# ツール定義
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search company knowledge base",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "category": {"type": "string", "enum": ["product", "support", "general"]}
                }
            }
        }
    }
]

# LLM設定
llm = openai.LLM(
    model="gpt-4o-mini",
    tools=tools
)
```

### 5. パフォーマンス最適化

#### 5.1 キャッシュ戦略
- [ ] Redis等を使用したキャッシュレイヤー
- [ ] TTL（Time To Live）設定
- [ ] キャッシュ無効化戦略

#### 5.2 非同期処理の最適化
```python
async def parallel_api_calls(query: str):
    """複数のAPIを並行実行"""
    tasks = [
        self.call_api_1(query),
        self.call_api_2(query),
        self.search_rag(query)
    ]
    results = await asyncio.gather(*tasks)
    return combine_results(results)
```

### 6. エラーハンドリングと信頼性

#### 6.1 リトライ機構
```python
@retry(max_attempts=3, backoff_factor=2)
async def call_external_api_with_retry(self, endpoint: str, data: dict):
    """リトライ機能付きAPI呼び出し"""
    pass
```

#### 6.2 フォールバック処理
- [ ] 外部API障害時のフォールバック応答
- [ ] 部分的な機能低下モード
- [ ] エラーログとモニタリング

### 7. セキュリティ考慮事項

#### 7.1 認証・認可
- [ ] APIキーの安全な管理
- [ ] ユーザー別のアクセス制御
- [ ] レート制限の実装

#### 7.2 データ保護
- [ ] センシティブ情報のマスキング
- [ ] 通信の暗号化
- [ ] 監査ログの実装

## 実装優先順位

### Phase 1: 基本実装（1-2週間）
1. Assistantクラスの拡張
2. 簡単な外部API連携（天気API等）
3. 基本的なエラーハンドリング

### Phase 2: RAG実装（2-3週間）
1. ベクトルDB統合
2. 知識ベース検索機能
3. キャッシュ機構の実装

### Phase 3: 高度な機能（3-4週間）
1. LLMツール機能の実装
2. 複数API並行実行
3. 高度なエラーハンドリング

### Phase 4: 本番対応（2-3週間）
1. セキュリティ強化
2. パフォーマンス最適化
3. モニタリング・ログ実装

## 技術スタック候補

### ベクトルデータベース
- Pinecone（マネージドサービス）
- ChromaDB（ローカル開発向け）
- Weaviate（セルフホスト可能）

### キャッシュ
- Redis
- Memcached

### モニタリング
- Prometheus + Grafana
- OpenTelemetry

### API Gateway
- Kong
- AWS API Gateway

## 参考実装

既存のagent-rag.pyでは、JSONファイルベースの簡易的なRAG実装が行われている。これを拡張して、より高度な検索機能を実装する。

```python
# 現在の実装
def load_knowledge_base() -> Dict[str, Any]:
    with open('test_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 拡張案
async def search_knowledge_base(query: str) -> List[Document]:
    embeddings = await generate_embeddings(query)
    results = await vector_db.similarity_search(embeddings)
    return results
```

## 注意事項

1. **レイテンシ管理**: 音声対話システムのため、応答遅延は最小限に抑える
2. **コンテキストサイズ**: LLMのトークン制限を考慮した設計
3. **コスト管理**: 外部API呼び出しとLLM使用のコスト最適化
4. **スケーラビリティ**: 将来的な負荷増大に対応できる設計

## 次のステップ

1. 技術選定の最終決定
2. プロトタイプの実装
3. パフォーマンステストの実施
4. 段階的な本番環境への適用