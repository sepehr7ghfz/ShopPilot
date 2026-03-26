# ShopPilot

ShopPilot is a multimodal AI shopping assistant MVP for a commerce experience.

It provides one unified assistant interface for:
- General conversation
- Text-based product recommendation
- Image-based product search
- Hybrid search (text + image)

The project is local-first, reviewer-friendly, and intentionally scoped for a take-home submission.

## What ShopPilot Does

ShopPilot accepts a user message, an uploaded image, or both, then routes internally to the right retrieval path while keeping a single assistant experience.

### Supported Use Cases

1. General conversation
2. Text recommendation over a local product catalog
3. Image similarity search over local catalog images
4. Hybrid recommendation by combining text and image signals

## Architecture Overview

High-level flow:
1. Frontend sends message and optional image to one backend endpoint.
2. Backend performs intent routing.
3. Service layer runs one of: general chat, text retrieval, image retrieval, hybrid retrieval.
4. Backend returns a consistent response contract for the UI.

### Why This Architecture

- Single assistant endpoint keeps the product experience unified.
- Thin API routes with service-oriented orchestration keep code maintainable.
- Local JSON + local files keep setup simple and reproducible.
- Rule-based routing and deterministic scoring are easy to explain in a take-home context.

## Technical Stack

Backend:
- Python 3.11+
- FastAPI
- Pydantic
- CLIP via Transformers + Torch (for image retrieval)

Frontend:
- Next.js (App Router)
- React + TypeScript
- Custom CSS (no UI framework)

Data:
- Local catalog JSON
- Local catalog images

## Project Structure

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
  frontend/
    src/
      app/
      components/
      lib/
      styles/
    public/placeholders/
    package.json
    .env.example
  .gitignore
  README.md
```

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### 1) Backend Setup

```bash
cd /Users/sepehr_ghfz/Desktop/ShopPilot
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Run backend:

```bash
cd /Users/sepehr_ghfz/Desktop/ShopPilot/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL: `http://localhost:8000`

### 2) Frontend Setup

```bash
cd /Users/sepehr_ghfz/Desktop/ShopPilot/frontend
cp .env.example .env.local
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`

## Environment Variables

Frontend:
- `NEXT_PUBLIC_API_BASE_URL` (example in [frontend/.env.example](frontend/.env.example))

Backend (optional, with defaults):
- `APP_NAME`
- `APP_VERSION`
- `DEBUG`
- `LOG_LEVEL`
- `API_PREFIX`

## API Overview

Base URL: `http://localhost:8000`

### Health Endpoint

- `GET /health`

Example:

```bash
curl http://localhost:8000/health
```

### Unified Assistant Endpoint

- `POST /api/assistant/respond`
- `multipart/form-data`
- Fields:
  - `message` (optional string)
  - `image` (optional file)
  - `session_id` (optional string)
- Validation: at least one of `message` or `image` must be provided.

#### Text-only Request

```bash
curl -X POST http://localhost:8000/api/assistant/respond \
  -F "message=recommend me a black hoodie for casual wear" \
  -F "session_id=demo-session"
```

#### Image-only Request

```bash
curl -X POST http://localhost:8000/api/assistant/respond \
  -F "image=@/absolute/path/to/image.jpg" \
  -F "session_id=demo-session"
```

#### Text + Image Request (Hybrid)

```bash
curl -X POST http://localhost:8000/api/assistant/respond \
  -F "message=find similar items but more casual" \
  -F "image=@/absolute/path/to/image.jpg" \
  -F "session_id=demo-session"
```

#### Example Response Shape

```json
{
  "response_text": "I found 5 strong options for your request. Top picks: Metro Fleece Hoodie, Core Zip Hoodie, Stride Performance Tee.",
  "intent": "text_recommendation",
  "products": [
    {
      "id": "hoodie-001",
      "name": "Metro Fleece Hoodie",
      "category": "hoodie",
      "price": 68.0,
      "description": "Warm fleece-lined hoodie with a relaxed fit for street and casual outfits.",
      "image_path": "catalog/images/hoodie_metro_fleece_black.jpg",
      "reason": "category match (hoodie); tag match: casual, black"
    }
  ]
}
```

## MVP Limitations

- Catalog is local and static (no admin panel, no dynamic sync).
- Text retrieval is deterministic metadata scoring (no semantic embeddings yet).
- Image retrieval depends on local CLIP dependencies and local catalog images.
- No authentication or user account state.
- No production-grade observability stack yet.

## Future Improvements

- Add semantic text embeddings for stronger recommendation quality.
- Add product image serving and CDN-ready image URLs.
- Add conversation persistence and richer session memory.
- Add lightweight evaluation scripts and benchmark set.
- Add containerized deployment profile.

## Deployment Readiness Notes

Current structure is deployment-friendly but intentionally local-first.

Already in place:
- Clear API boundaries and schemas
- Environment-based configuration
- Frontend-backend separation
- Service-layer modularity

Before production deployment:
- Add persistent storage and media hosting
- Add request auth/rate limiting
- Add structured monitoring and alerting
- Add CI checks and automated tests
