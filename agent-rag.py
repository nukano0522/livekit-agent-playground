from livekit.plugins import openai

from dotenv import load_dotenv
import json
import os
from typing import Dict, Any, List
import chromadb
from openai import OpenAI, AzureOpenAI

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, llm
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# 環境変数をクリアして.envファイルから再読み込み
env_vars_to_clear = [
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "OPENAI_API_VERSION",
    "AZURE_OPENAI_ENDPOINT_EM",
    "AZURE_OPENAI_API_KEY_EM",
    "OPENAI_API_VERSION_EM"
]

for var in env_vars_to_clear:
    if var in os.environ:
        del os.environ[var]

# .envファイルを強制的に再読み込み
load_dotenv(override=True)


class RAGAssistant(Agent):
    def __init__(self, chat_ctx: ChatContext = None, chroma_collection=None, openai_client=None, embedding_model=None) -> None:
        instructions = """あなたはライブキット株式会社のAIアシスタントです。
        ユーザーの質問に対して、検索された関連情報を基に正確に答えてください。
        検索結果に情報がない場合は、その旨を伝えてください。
        日本語で丁寧に応答してください。"""
        
        super().__init__(instructions=instructions, chat_ctx=chat_ctx)
        self.chroma_collection = chroma_collection
        self.openai_client = openai_client
        self.embedding_model = embedding_model
    
    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """ユーザーの発話が完了した際に、ChromaDBで検索を実行し、
        関連情報をコンテキストに追加する"""
        print(f"\n[DEBUG] on_user_turn_completed called with: {new_message.content}")
        
        if self.chroma_collection and new_message.content:
            print(f"[DEBUG] ChromaDB collection is available")
            try:
                # ユーザーの質問をembeddingに変換
                user_query = new_message.content
                print(f"[DEBUG] Creating embedding for query: {user_query}")
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=user_query
                )
                query_embedding = response.data[0].embedding
                print(f"[DEBUG] Embedding created successfully")
                
                # ChromaDBで類似ドキュメントを検索
                print(f"[DEBUG] Searching ChromaDB...")
                results = self.chroma_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=3
                )
                print(f"[DEBUG] Search completed. Found {len(results['documents'][0])} results")
                
                # 検索結果をコンテキストに追加
                if results['documents'][0]:
                    context = "\n\n関連情報:\n"
                    for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
                        print(f"[DEBUG] Result {i+1} (distance: {distance:.4f}): {doc[:100]}...")
                        context += f"\n{i+1}. {doc}\n"
                    
                    # new_messageの内容を更新（検索結果を含めた形に）
                    enhanced_content = f"{context}\n\nユーザーの質問: {user_query}"
                    new_message.content = enhanced_content
                    print(f"[DEBUG] Enhanced message content with search results")
                else:
                    print(f"[DEBUG] No search results found")
            except Exception as e:
                print(f"[ERROR] Exception in on_user_turn_completed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[DEBUG] ChromaDB collection is NOT available or no message content")
        
        # 親クラスのメソッドを呼び出す
        await super().on_user_turn_completed(turn_ctx, new_message)


def initialize_chromadb_client():
    """ChromaDBクライアントとOpenAIクライアントを初期化"""
    print("\n[DEBUG] Initializing ChromaDB client...")
    # ChromaDBクライアントを初期化
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # Embedding用のAzure OpenAI APIキーが設定されている場合はそれを使用
    if os.environ.get("AZURE_OPENAI_API_KEY_EM") and os.environ.get("AZURE_OPENAI_ENDPOINT_EM"):
        openai_client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY_EM"),
            api_version=os.environ.get("OPENAI_API_VERSION_EM", "2024-08-01-preview"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT_EM")
        )
        embedding_model = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        print(f"Azure OpenAI API (Embedding専用)を使用します (Embeddingモデル: {embedding_model})")
    # 通常のAzure OpenAI APIキーが設定されている場合
    elif os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get("AZURE_OPENAI_ENDPOINT"):
        openai_client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version=os.environ.get("OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        embedding_model = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        print(f"Azure OpenAI APIを使用します (Embeddingモデル: {embedding_model})")
    else:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        embedding_model = "text-embedding-3-small"
        print("OpenAI APIを使用します")
    
    # コレクションを取得
    try:
        collection = chroma_client.get_collection(name="livekit_knowledge")
        doc_count = collection.count()
        print(f"[DEBUG] ChromaDBコレクション 'livekit_knowledge' を読み込みました。ドキュメント数: {doc_count}")
        
        # テストクエリで動作確認
        print("[DEBUG] テストクエリを実行中...")
        test_embedding = openai_client.embeddings.create(
            model=embedding_model,
            input="価格を教えてください"
        ).data[0].embedding
        
        test_results = collection.query(
            query_embeddings=[test_embedding],
            n_results=3
        )
        print(f"[DEBUG] テストクエリ結果: {len(test_results['documents'][0])} 件のドキュメントが見つかりました")
        for i, doc in enumerate(test_results['documents'][0]):
            print(f"[DEBUG] テスト結果 {i+1}: {doc[:100]}...")
            
    except Exception as e:
        print(f"[ERROR] ChromaDBコレクションの読み込みエラー: {e}")
        print("init_chromadb.pyを実行してデータベースを初期化してください。")
        collection = None
    
    return collection, openai_client, embedding_model

async def entrypoint(ctx: agents.JobContext):
    # ChromaDBとOpenAIクライアントを初期化
    chroma_collection, openai_client, embedding_model = initialize_chromadb_client()
    
    # 初期コンテキストを作成
    initial_ctx = ChatContext()
    
    # Azure OpenAI APIキーが設定されている場合はAzureを使用
    if os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get("AZURE_OPENAI_ENDPOINT"):
        session = AgentSession(
            stt=openai.STT.with_azure(
                model="gpt-4o-transcribe",
            ),
            llm=openai.LLM.with_azure(model="gpt-4o-mini"),
            tts=openai.TTS.with_azure(
                model="gpt-4o-mini-tts",
                voice="ash",
                instructions="Speak in a friendly and conversational tone.",
            ),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
        )
    else:
        session = AgentSession(
            stt=openai.STT(
                model="gpt-4o-transcribe",
            ),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(
                model="gpt-4o-mini-tts",
                voice="ash",
                instructions="Speak in a friendly and conversational tone.",
            ),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
        )

    await session.start(
        room=ctx.room,
        agent=RAGAssistant(
            chat_ctx=initial_ctx,
            chroma_collection=chroma_collection,
            openai_client=openai_client,
            embedding_model=embedding_model
        ),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="ユーザーに日本語で挨拶し、ライブキット株式会社について質問があれば答えられることを伝えてください。ChromaDBベクトル検索を使用して回答することも伝えてください。"
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
