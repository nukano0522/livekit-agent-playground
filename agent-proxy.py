from livekit.plugins import openai

from dotenv import load_dotenv
import os
import httpx

from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins import (
    openai,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# 環境変数をクリアして.envファイルから再読み込み
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]
if "AZURE_OPENAI_API_KEY" in os.environ:
    del os.environ["AZURE_OPENAI_API_KEY"]
if "AZURE_OPENAI_ENDPOINT" in os.environ:
    del os.environ["AZURE_OPENAI_ENDPOINT"]
if "OPENAI_API_VERSION" in os.environ:
    del os.environ["OPENAI_API_VERSION"]

# .envファイルを強制的に再読み込み
load_dotenv(override=True)
# print("OPENAI_API_KEY: {}".format(os.environ.get("OPENAI_API_KEY")))
# print("AZURE_OPENAI_API_KEY: {}".format(os.environ.get("AZURE_OPENAI_API_KEY")))


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")


async def entrypoint(ctx: agents.JobContext):
    # プロキシ設定を取得
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    proxy_url = https_proxy or http_proxy
    
    # プロキシ付きのHTTPクライアントを作成
    http_client = None
    if proxy_url:
        http_client = httpx.AsyncClient(
            proxy=proxy_url,
            timeout=httpx.Timeout(connect=15.0, read=5.0, write=5.0, pool=5.0),
        )
        print(f"プロキシを使用: {proxy_url}")
    else:
        print("プロキシなしで直接接続")
    
    # Azure OpenAI APIキーが設定されている場合はAzureを使用
    if os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get("AZURE_OPENAI_ENDPOINT"):
        session = AgentSession(
            stt=openai.STT.with_azure(
                model="gpt-4o-transcribe",
                http_session=http_client,
            ),
            llm=openai.LLM.with_azure(
                model="gpt-4o-mini",
                http_session=http_client,
            ),
            tts=openai.TTS.with_azure(
                model="gpt-4o-mini-tts",
                voice="ash",
                instructions="Speak in a friendly and conversational tone.",
                http_session=http_client,
            ),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
        )
    else:
        session = AgentSession(
            stt=openai.STT(
                model="gpt-4o-transcribe",
                http_session=http_client,
            ),
            llm=openai.LLM(
                model="gpt-4o-mini",
                http_session=http_client,
            ),
            tts=openai.TTS(
                model="gpt-4o-mini-tts",
                voice="ash",
                instructions="Speak in a friendly and conversational tone.",
                http_session=http_client,
            ),
            vad=silero.VAD.load(),
            turn_detection=MultilingualModel(),
        )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    # LiveKitサーバーへの接続時はプロキシを使わないようにする
    # Worker起動前にプロキシ環境変数を一時的に無効化
    original_http_proxy = os.environ.get("HTTP_PROXY")
    original_https_proxy = os.environ.get("HTTPS_PROXY")
    
    if "HTTP_PROXY" in os.environ:
        del os.environ["HTTP_PROXY"]
    if "HTTPS_PROXY" in os.environ:
        del os.environ["HTTPS_PROXY"]
    if "http_proxy" in os.environ:
        del os.environ["http_proxy"]
    if "https_proxy" in os.environ:
        del os.environ["https_proxy"]
    
    # WorkerOptionsを作成（プロキシなしで）
    worker_options = agents.WorkerOptions(entrypoint_fnc=entrypoint)
    
    # プロキシ環境変数を復元（entrypoint内で使用するため）
    if original_http_proxy:
        os.environ["HTTP_PROXY"] = original_http_proxy
        os.environ["http_proxy"] = original_http_proxy
    if original_https_proxy:
        os.environ["HTTPS_PROXY"] = original_https_proxy
        os.environ["https_proxy"] = original_https_proxy
    
    # Workerを起動
    agents.cli.run_app(worker_options)