# ShopPilot

ShopPilot is a multimodal commerce assistant that supports one unified conversation flow for:

1. General chat
2. Text-based recommendation
3. Image-based similarity search
4. Hybrid search using text plus image

The project is designed as a clean, reviewer-friendly MVP with production-style structure and containerized deployment.

## Highlights

1. Single assistant endpoint for all interaction modes
2. LLM tool orchestration with deterministic fallback retrieval
3. Semantic text retrieval and image similarity retrieval
4. Cart-aware assistant responses with UI cart actions
5. Dockerized backend, frontend, and nginx reverse proxy

## Live Deployment

1. Deployed on AWS EC2
2. Public URL: http://35.182.8.63
3. Current public endpoint is HTTP

## System Architecture

Request flow:

1. Browser sends user message and optional image to frontend API route
2. Frontend forwards multipart request to backend unified assistant endpoint
3. Backend agent chooses response path:
   1. Direct chat response
   2. Text retrieval
   3. Image retrieval
   4. Hybrid retrieval
4. Backend returns a consistent response contract
5. Frontend renders response text, product cards, and cart actions

Service layout:

1. API routes for assistant and health
2. Agent orchestration service for intent and tool routing
3. Retrieval services for text, image, and hybrid ranking
4. Shared schemas and utilities for contracts and catalog access

## Tech Stack

Backend:

1. Python 3.11
2. FastAPI
3. Pydantic
4. OpenAI SDK
5. Sentence Transformers for semantic text embeddings
6. CLIP stack with Transformers and Torch for image similarity

Frontend:

1. Next.js 14 App Router
2. React 18 and TypeScript
3. Custom CSS

Infra:

1. Docker and Docker Compose
2. Nginx reverse proxy
3. AWS EC2 deployment

Data:

1. Local product catalog JSON
2. Local product image files served via media endpoint

## Repository Structure

```text
ShopPilot/
  backend/
    app/
      api/routes/
      core/
      schemas/
      services/
      utils/
      main.py
    data/catalog/
      products.json
      images/
    requirements.txt
    Dockerfile
  frontend/
    src/
      app/
      components/
      lib/
      styles/
    public/
    package.json
    Dockerfile
  deploy/
    nginx.conf
  docker-compose.yml
  .dockerignore
  EC2_DEPLOY_COMMANDS.md
```

## Local Development

Prerequisites:

1. Python 3.11+
2. Node.js 18+
3. npm

Backend setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend setup:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Local URLs:

1. Frontend: http://localhost:3000
2. Backend: http://localhost:8000
3. Health: http://localhost:8000/health

## Environment Variables

Backend:

1. OPENAI_API_KEY
2. OPENAI_MODEL
3. USE_LLM_ORCHESTRATOR
4. USE_TEXT_RAG
5. RAG_MODEL_NAME
6. SESSION_MEMORY_TURNS
7. API_PREFIX
8. LOG_LEVEL

Frontend runtime:

1. BACKEND_API_BASE_URL
2. BACKEND_REQUEST_TIMEOUT_MS

Frontend build:

1. NEXT_PUBLIC_MEDIA_BASE_URL

## API Contract

Dedicated API reference:

1. See [docs/AGENT_API.md](docs/AGENT_API.md) for full endpoint documentation, payloads, and response schema.

Unified assistant endpoint:

1. Method: POST
2. Path: /api/assistant/respond
3. Content type: multipart/form-data
4. Fields:
   1. message optional
   2. image optional
   3. session_id optional

Health endpoint:

1. Method: GET
2. Path: /health

Example request:

```bash
curl -X POST http://localhost:8000/api/assistant/respond \
  -F "message=recommend daily wear sneakers" \
  -F "session_id=demo"
```

## Docker Deployment

Start full stack:

```bash
docker compose up -d --build
```

Verify:

```bash
docker compose ps
docker compose logs --tail 120
curl -sS http://127.0.0.1/
curl -sS -X POST http://127.0.0.1/api/assistant/respond -F "message=hello" -F "session_id=health-check"
```

## AWS EC2 Notes

1. The app is served over HTTP on port 80 through nginx
2. Security Group requires inbound port 80 and port 22
3. Use Elastic IP for stable public access
4. HTTPS is a separate step requiring domain and TLS certificate

## Operational Troubleshooting

If product images do not appear:

1. Verify media path is reachable:

```bash
curl -I http://127.0.0.1/media/catalog/images/hf-15970.jpg
```

2. Check nginx and backend logs:

```bash
docker compose logs --tail 120 nginx backend
```

3. Rebuild frontend if stale assets are suspected:

```bash
docker compose build --no-cache frontend
docker compose up -d frontend nginx
```

If host disk fills after many rebuilds:

```bash
docker image prune -f
docker builder prune -af
```

## Security Checklist

1. Never commit secrets to git
2. Store API keys only in environment files on server
3. Rotate exposed keys immediately
4. Restrict SSH access by source IP
5. Add HTTPS before public production use

## Roadmap

1. Add authentication and per-user persistence
2. Add monitoring and alerting
3. Add CI with tests and lint gates
4. Add domain plus automated TLS
5. Add object storage or CDN for media at scale
