# ビルドステージ
FROM node:20-alpine AS builder

WORKDIR /app

# 依存関係をコピー・インストール
COPY web-client/package*.json ./
RUN npm ci

# ソースコードをコピー・ビルド
COPY web-client/ .
RUN npm run build

# 実行ステージ
FROM nginx:alpine

# ビルド成果物をコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx設定をコピー
COPY docker/web-client/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000