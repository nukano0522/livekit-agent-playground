from livekit.plugins import openai

from dotenv import load_dotenv
import os

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
        agent=Assistant(),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
