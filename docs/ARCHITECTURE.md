# ShopPilot Architecture

## 1. Purpose

ShopPilot is a multimodal shopping assistant that unifies conversation, text recommendation, image similarity search, and hybrid retrieval behind one assistant experience.

Primary goals:

1. Keep the product experience simple with one assistant endpoint
2. Preserve explainability with deterministic retrieval components
3. Improve quality with LLM orchestration and semantic retrieval
4. Stay deployable with a lightweight container stack

## 2. High-Level System

Core components:

1. Frontend: Next.js chat interface
2. Frontend proxy route: forwards assistant requests to backend
3. Backend API: FastAPI unified assistant endpoint
4. Agent orchestration: intent handling and tool routing
5. Retrieval services:
   1. Text retrieval
   2. Image retrieval
   3. Hybrid retrieval
6. Local catalog storage:
   1. JSON metadata
   2. Local image files
7. Reverse proxy: Nginx
8. Runtime: Docker Compose on AWS EC2

## 3. Request Lifecycle

### 3.1 Text-only query

1. User submits text in chat UI
2. Frontend sends multipart request to frontend API route
3. Frontend API route forwards request to backend assistant endpoint
4. Agent service selects path:
   1. Direct chat response, or
   2. Text retrieval tool flow
5. Backend returns response_text, intent, products, cart_actions
6. Frontend renders assistant response and product cards

### 3.2 Image-only query

1. User uploads image without text
2. Backend computes embedding through CLIP pipeline
3. Similarity search ranks catalog images/products
4. Backend returns image_search response

### 3.3 Hybrid query

1. User submits text and image together
2. Backend computes text and image signals
3. Hybrid service fuses scores and applies constraints
4. Final ranked products returned with rationale

## 4. Backend Architecture

Backend organization:

1. API layer:
   1. Health route
   2. Assistant route
2. Core layer:
   1. Settings and environment configuration
   2. Logging setup
3. Schemas:
   1. Request and response contracts
   2. Product and cart action types
4. Services:
   1. Agent orchestration and fallback logic
   2. Intent routing
   3. Text retrieval
   4. Image retrieval
   5. Hybrid retrieval
   6. Query constraints parsing

Key design choice:

1. One assistant endpoint with internal routing keeps frontend simple and allows incremental backend improvements without API sprawl.

## 5. Retrieval Design

### 5.1 Text retrieval

Uses combined retrieval strategy:

1. Semantic signal from Sentence Transformers embeddings
2. Lexical/tag/category matching signal
3. Fusion scoring for robust ranking

### 5.2 Image retrieval

1. Query image encoded with CLIP-compatible embedding flow
2. Catalog images represented in same embedding space
3. Similarity scoring returns nearest products

### 5.3 Hybrid retrieval

1. Text and image scores are normalized
2. Weighted fusion combines both signals
3. Query constraints (such as budget) are applied before final ranking

## 6. Frontend Architecture

Frontend responsibilities:

1. Chat interaction and message state
2. Message rendering and formatting
3. Product card rendering
4. Cart panel behavior and cart action application
5. Drag-and-drop image support
6. Frontend proxy route to backend

Rendering notes:

1. Product images are resolved to media URLs served behind nginx
2. Product card image rendering bypasses optimizer path where needed for deployment compatibility

## 7. Deployment Architecture

Runtime topology on EC2:

1. Nginx container exposed on port 80
2. Frontend container on internal port 3000
3. Backend container on internal port 8000
4. Nginx routes:
   1. / to frontend
   2. /api and /media to backend

Why this topology:

1. Single public entry point
2. Simple service isolation
3. Clean path-based routing
4. Easy local and server parity with docker compose

## 8. Data Architecture

1. Product metadata in backend/data/catalog/products.json
2. Product images in backend/data/catalog/images/
3. Media served by backend static mount at /media
4. Frontend consumes product image_path and resolves to runtime media URL

## 9. Reliability and Operations

1. Health route for liveness check
2. Structured logs across frontend proxy, backend, and nginx
3. Containerized rebuild and restart workflow
4. Known operational constraint: small EC2 instances can be resource-starved during build
5. Maintenance: periodic image and builder cache pruning

## 10. Security Posture (Current MVP)

Current state:

1. Environment-variable secret injection
2. No auth on assistant endpoint
3. HTTP-only deployment by default

Recommended hardening steps:

1. Rotate exposed keys immediately when needed
2. Add HTTPS with domain and TLS
3. Restrict SSH ingress to fixed source IP
4. Add rate limiting and request authentication if external usage grows

## 11. Trade-offs and Decisions

1. Unified endpoint over multiple specialized endpoints:
   1. Pro: simpler client integration
   2. Con: backend orchestration complexity
2. Local catalog storage over managed vector database:
   1. Pro: reproducible and reviewer-friendly
   2. Con: limited scale and operational features
3. Deterministic fallback plus LLM orchestration:
   1. Pro: resilient behavior when model path fails
   2. Con: more service logic to maintain

## 12. Future Architecture Evolution

1. Add persistent vector index storage
2. Add managed object storage or CDN for media
3. Add auth and multi-tenant session persistence
4. Add observability stack with metrics and tracing
5. Add CI pipeline with integration and contract tests
