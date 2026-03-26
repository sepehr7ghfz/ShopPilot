# ShopPilot EC2 Deploy Commands

Use these commands directly on your EC2 terminal.

## 1) Clone or update the repo

```bash
cd ~
if [ -d ShopPilot ]; then
  cd ShopPilot
  git fetch --all
  git pull --rebase origin main
else
  git clone https://github.com/sepehr7ghfz/ShopPilot.git
  cd ShopPilot
fi
```

## 2) Create runtime env file

```bash
cd ~/ShopPilot
cat > .env << 'EOF'
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
OPENAI_MODEL=gpt-4o-mini
USE_LLM_ORCHESTRATOR=true
USE_TEXT_RAG=true
RAG_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
SESSION_MEMORY_TURNS=8
LOG_LEVEL=INFO
BACKEND_REQUEST_TIMEOUT_MS=60000
EOF
```

## 3) Build and start the stack

```bash
cd ~/ShopPilot
docker compose down
docker compose up -d --build
docker compose ps
```

## 4) Follow logs

```bash
cd ~/ShopPilot
docker compose logs -f --tail=150
```

## 5) Quick checks

```bash
# Backend health (inside EC2)
curl -s http://127.0.0.1/api/health

# Frontend over nginx (inside EC2)
curl -I http://127.0.0.1/
```

## 6) Find your public URL

From AWS Console:
- EC2
- Instances
- Copy Public IPv4 address

Open in browser:
- http://YOUR_PUBLIC_IP

## 7) Update after new commits

```bash
cd ~/ShopPilot
git fetch --all
git pull --rebase origin main
docker compose down
docker compose up -d --build
docker compose ps
```

## 8) Useful troubleshooting

```bash
# Show container status
cd ~/ShopPilot && docker compose ps

# Show recent logs from one service
cd ~/ShopPilot && docker compose logs --tail=200 backend
cd ~/ShopPilot && docker compose logs --tail=200 frontend
cd ~/ShopPilot && docker compose logs --tail=200 nginx

# Restart stack
cd ~/ShopPilot && docker compose restart

# Rebuild from scratch
cd ~/ShopPilot && docker compose down --remove-orphans
cd ~/ShopPilot && docker compose build --no-cache
cd ~/ShopPilot && docker compose up -d
```

## 9) If port 80 is blocked

Check EC2 Security Group inbound rules:
- TCP 22 from My IP
- TCP 80 from Anywhere
- TCP 443 from Anywhere

## 10) Final reminder

Replace YOUR_OPENAI_KEY_HERE in .env before first run.
