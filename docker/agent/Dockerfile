FROM python:3.11-slim

WORKDIR /app

# 音声処理用のシステムパッケージをインストール
RUN apt-get update && \
    apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY agent.py agent-rag.py agent-proxy.py init_chromadb.py ./
COPY test_data_extended.json test_data.json ./

# ChromaDBディレクトリを作成
RUN mkdir -p chroma_db

# 必要なモデルをダウンロード
RUN python agent.py download-files

# デフォルトコマンド
CMD ["python", "agent.py", "dev"]