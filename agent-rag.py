from livekit.plugins import openai

from dotenv import load_dotenv
import json
import os
from typing import Dict, Any

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv()


class RAGAssistant(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        instructions = """あなたはライブキット株式会社のAIアシスタントです。
        提供された会社情報を基に、正確に質問に答えてください。
        日本語で丁寧に応答してください。"""
        
        super().__init__(instructions=instructions, chat_ctx=chat_ctx)


def load_knowledge_base() -> Dict[str, Any]:
    """テストデータを読み込む"""
    try:
        with open('test_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return {}

def format_knowledge_base(knowledge: Dict[str, Any]) -> str:
    """知識ベースを読みやすい形式にフォーマット"""
    formatted_content = []
    
    # 会社情報
    company = knowledge.get('company_info', {})
    formatted_content.append("【会社情報】")
    formatted_content.append(f"会社名: {company.get('name')}")
    formatted_content.append(f"設立: {company.get('founded')}")
    formatted_content.append(f"本社: {company.get('headquarters')}")
    formatted_content.append(f"従業員数: {company.get('employees')}")
    formatted_content.append(f"サービス: {', '.join(company.get('services', []))}")
    
    # 製品情報
    formatted_content.append("\n【製品情報】")
    for product in knowledge.get('products', []):
        formatted_content.append(f"\n◆ {product['name']}")
        formatted_content.append(f"  説明: {product['description']}")
        if 'features' in product:
            formatted_content.append(f"  機能: {', '.join(product['features'])}")
        if 'pricing' in product:
            formatted_content.append(f"  価格: {product['pricing']}")
        if 'supported_models' in product:
            formatted_content.append(f"  対応モデル: {', '.join(product['supported_models'])}")
        if 'use_cases' in product:
            formatted_content.append(f"  ユースケース: {', '.join(product['use_cases'])}")
    
    # 技術仕様
    tech = knowledge.get('technical_specs', {})
    formatted_content.append("\n【技術仕様】")
    formatted_content.append(f"プロトコル: {', '.join(tech.get('protocols', []))}")
    formatted_content.append(f"対応プラットフォーム: {', '.join(tech.get('supported_platforms', []))}")
    formatted_content.append(f"プログラミング言語: {', '.join(tech.get('programming_languages', []))}")
    formatted_content.append(f"最大参加者数/ルーム: {tech.get('max_participants_per_room')}")
    formatted_content.append(f"レイテンシ: {tech.get('latency')}")
    
    # サポート情報
    support = knowledge.get('support', {})
    formatted_content.append("\n【サポート情報】")
    formatted_content.append(f"ドキュメント: {support.get('documentation')}")
    formatted_content.append(f"コミュニティ: {support.get('community')}")
    formatted_content.append(f"エンタープライズ: {support.get('enterprise')}")
    
    return '\n'.join(formatted_content)

async def entrypoint(ctx: agents.JobContext):
    # 知識ベースを読み込む
    knowledge_base = load_knowledge_base()
    
    # 初期コンテキストを作成
    initial_ctx = ChatContext()
    
    # 知識ベースの情報をコンテキストに追加
    knowledge_content = format_knowledge_base(knowledge_base)
    initial_ctx.add_message(
        role="assistant",
        content=f"以下は参照すべきライブキット株式会社の情報です:\n\n{knowledge_content}\n\nこの情報を基に、ユーザーの質問に正確に答えてください。"
    )
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
        agent=RAGAssistant(chat_ctx=initial_ctx),
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="ユーザーに日本語で挨拶し、ライブキット株式会社について質問があれば答えられることを伝えてください。"
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
