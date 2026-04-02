FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies first (cached layer)
COPY web/package*.json ./web/
RUN cd web && npm install

# Copy source — web app and shared TS contracts it imports
COPY web/ ./web/
COPY shared/ ./shared/

# NEXT_PUBLIC_* vars must be present at build time (Next.js bakes them in)
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_API_KEY
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_KEY=$NEXT_PUBLIC_API_KEY

RUN cd web && npm run build

# ── Runtime image ─────────────────────────────────────────────────────────────
FROM node:20-alpine
WORKDIR /app/web

COPY --from=builder /app/web/.next ./.next
COPY --from=builder /app/web/node_modules ./node_modules
COPY --from=builder /app/web/package.json ./package.json
COPY --from=builder /app/web/public ./public

EXPOSE 3000
CMD ["node_modules/.bin/next", "start", "--hostname", "0.0.0.0", "--port", "3000"]
