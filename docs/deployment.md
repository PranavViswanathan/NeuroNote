# NeuroNote — Production Deployment Guide

This guide deploys NeuroNote to a VPS using the existing Docker Compose stack with Caddy as a TLS-terminating reverse proxy. Total cost: ~€4–6/month. Your Anthropic API key stays on the server and is never exposed to users.

---

## Architecture

```
Internet
  │
  ▼ port 80/443
Caddy (TLS, auto Let's Encrypt)
  ├── /v1/*      → FastAPI (api:8000)
  ├── /health    → FastAPI (api:8000)
  ├── /docs*     → FastAPI (api:8000)
  └── /*         → Next.js (web:3000)
                        │
                        └── calls /v1/* (same domain = same origin, no CORS)
```

All four containers (db, api, web, caddy) run in a single Docker Compose stack. The VPS firewall exposes only ports 80 and 443; database and API ports are internal-only.

---

## Prerequisites

- A domain name you control (e.g. `notes.yourdomain.com`)
- Your Anthropic API key
- ~15 minutes

---

## Step 1 — Provision a VPS

**Hetzner CX22** (~€4/mo, recommended) or **DigitalOcean Basic Droplet** (~$6/mo):
- OS: **Ubuntu 22.04**
- 2 vCPU, 4 GB RAM, 40 GB SSD
- Enable backups (~€0.80/mo extra, worth it)

Note the public IP address after provisioning.

---

## Step 2 — Point DNS to the VPS

In your DNS provider, add an **A record**:

| Type | Name | Value | TTL |
|---|---|---|---|
| A | `notes.yourdomain.com` | `<VPS IP>` | 300 |

Check propagation before proceeding:
```bash
dig +short notes.yourdomain.com
# Should return the VPS IP
```

Caddy needs the domain to resolve in order to obtain a TLS certificate from Let's Encrypt.

---

## Step 3 — Configure the VPS

SSH into the VPS as root, then:

```bash
# Firewall: allow only SSH, HTTP, HTTPS
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw enable

# Install Docker (includes the Compose plugin)
curl -fsSL https://get.docker.com | sh
```

Verify:
```bash
docker compose version
# Docker Compose version v2.x.x
```

---

## Step 4 — Clone the repo and configure secrets

```bash
git clone https://github.com/RoyaleRishi/NeuroNote.git
cd NeuroNote
cp infra/.env.prod.example infra/.env.prod
nano infra/.env.prod
```

Fill in all required values. Generate strong random secrets with:
```bash
openssl rand -hex 32
```

Your `.env.prod` should look like:
```
DOMAIN=notes.yourdomain.com
API_KEY=a3f9c2d1e8b7f4...       # API header key — used by internal service calls
LLM_API_KEY=sk-ant-...          # your LLM provider key, server-side only
LLM_BASE_URL=                   # optional: defaults to https://api.anthropic.com/v1/
DB_PASSWORD=8b7e4f1c2a9d3e...
NLP_EXTRACTION_PROFILE=llm-enhanced

# Password gate for the web UI (recommended for public deployments)
APP_PASSWORD=choose-a-strong-password   # what users type at the login screen
SESSION_SECRET=                         # openssl rand -hex 32
```

`LLM_BASE_URL` defaults to `https://api.anthropic.com/v1/`. Set it to any OpenAI-compatible endpoint (OpenAI, Groq, Mistral, Ollama, etc.) and update `NLP_LLM_MODEL` to match. `APP_PASSWORD` and `SESSION_SECRET` are optional but strongly recommended for public deployments.

**Never commit `.env.prod` to git.** It is in `.gitignore`.

---

## Step 5 — Deploy

```bash
make deploy-prod
```

This builds all images and starts the stack. First run takes 5–10 minutes (compiling the custom Postgres with AGE extension from source and building the Next.js app). Subsequent deploys are much faster due to Docker layer caching.

Watch the startup:
```bash
make prod-logs
```

Wait until you see Caddy log something like:
```
caddy | certificate obtained successfully
```

---

## Step 6 — Run database migrations

```bash
make prod-migrate
```

This is idempotent — safe to run on every deploy.

---

## Step 7 — Verify

```bash
# Health check
curl https://notes.yourdomain.com/health
# {"status":"ok"}

# API (replace with your API_KEY)
curl -H "X-Api-Key: <API_KEY>" https://notes.yourdomain.com/v1/notes
# {"items":[], ...}
```

Open `https://notes.yourdomain.com` in a browser — the app should load.

---

## Step 8 — Share with friends and family

Share two things:
1. **URL**: `https://notes.yourdomain.com`
2. **Password**: the `APP_PASSWORD` value from `.env.prod`

They type the password once. A browser session cookie is set automatically and clears when the browser is closed.

**Your Anthropic key is safe**: it lives only in the API container's environment, is never included in any response, and cannot be extracted from the browser.

---

## Ongoing operations

### Update to a new version
```bash
git pull
make deploy-prod    # rebuilds changed images, rolls services
make prod-migrate   # apply any new DB migrations
```

### View logs
```bash
make prod-logs

# Single service:
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml \
  --env-file infra/.env.prod logs -f api
```

### Stop the stack
```bash
make prod-down
```

### Database backup
```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml \
  --env-file infra/.env.prod \
  exec db pg_dump -U neuronote neuronote > neuronote-backup-$(date +%Y%m%d).sql
```

Run this before every update. Store backups off the VPS (download to your machine or copy to cloud storage).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Caddy `failed to obtain certificate` | DNS not propagated — wait and retry; check `dig`; confirm ports 80/443 open in firewall |
| App returns 403 Forbidden | `API_KEY` mismatch — the key in `.env.prod` changed after `web` was built; run `make deploy-prod` to rebuild |
| `npm run build` hangs or times out | First build on a small VPS can take 5+ min; wait it out; subsequent builds are fast |
| Migrations fail with `relation does not exist` | DB extensions not enabled — run: `docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml --env-file infra/.env.prod exec db psql -U neuronote -d neuronote -f /docker-entrypoint-initdb.d/001-enable-extensions.sql` then retry `make prod-migrate` |
| Graph features not working | Verify AGE extension is enabled (see above) |
| AI insight panel shows config hint | `LLM_API_KEY` is empty or wrong in `.env.prod` — fix and run `make deploy-prod` |
| VPS runs out of memory during build | Hetzner CX22 (4 GB) is the minimum; upgrade to CX32 (8 GB) if builds consistently fail |
| Always redirected to `/login` even after correct password | `SESSION_SECRET` changed between deploys (or was empty and `APP_PASSWORD` changed) — existing cookies are invalidated; users must log in again after any secret rotation |
| Login page not appearing (loads directly) | `APP_PASSWORD` is not set in `.env.prod` — the gate is disabled by design; add the variable and run `make deploy-prod` |
| Concept insight shows "No notes mention this concept" for most nodes | Concept meta-classification has not run yet — process (or re-process) notes after deploying to build SYNONYM_OF/SUBTOPIC_OF edges. Check `docker compose logs api \| grep concept_meta`. |
