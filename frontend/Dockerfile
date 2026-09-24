# Build a partir da raiz do repo:
#   docker build -f frontend/Dockerfile --build-arg VITE_API_URL=https://seu-dominio/api -t tcc-frontend .
FROM node:20-bookworm-slim AS build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY frontend/Caddyfile /etc/caddy/Caddyfile
EXPOSE 80 443
