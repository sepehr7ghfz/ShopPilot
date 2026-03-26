# ShopPilot Agent API Reference

This document provides a focused API contract for the ShopPilot assistant backend.

## Base URLs

Local backend:

1. http://localhost:8000

Docker or EC2 through nginx:

1. http://<server-host>

## Authentication

Current MVP behavior:

1. No authentication is required.
2. Rate limiting is not enabled yet.

## Endpoints

### 1. Health Check

Method:

1. GET

Path:

1. /health

Description:

1. Returns service health status.

Example:

```bash
curl -sS http://localhost:8000/health
```

Success response:

```json
{
  "status": "healthy"
}
```

### 2. Unified Assistant Response

Method:

1. POST

Path:

1. /api/assistant/respond

Content type:

1. multipart/form-data

Fields:

1. message: optional string
2. image: optional image file
3. session_id: optional string

Validation rule:

1. At least one of message or image must be provided.

Supported modes through one endpoint:

1. General chat
2. Text recommendation
3. Image search
4. Hybrid search

#### Text-only example

```bash
curl -sS -X POST http://localhost:8000/api/assistant/respond \
  -F "message=recommend daily wear sneakers for men" \
  -F "session_id=demo-session"
```

#### Image-only example

```bash
curl -sS -X POST http://localhost:8000/api/assistant/respond \
  -F "image=@/absolute/path/to/query.jpg" \
  -F "session_id=demo-session"
```

#### Hybrid example

```bash
curl -sS -X POST http://localhost:8000/api/assistant/respond \
  -F "message=find similar but cheaper" \
  -F "image=@/absolute/path/to/query.jpg" \
  -F "session_id=demo-session"
```

## Response Schema

Assistant response shape:

```json
{
  "response_text": "string",
  "intent": "general_chat | text_recommendation | image_search | hybrid_search",
  "products": [
    {
      "id": "string",
      "name": "string",
      "category": "string",
      "price": 0,
      "description": "string",
      "image_path": "string",
      "image_url": "string",
      "reason": "string"
    }
  ],
  "cart_actions": [
    {
      "action": "add | remove | clear",
      "product_ids": ["string"],
      "note": "string"
    }
  ]
}
```

Field notes:

1. response_text: assistant natural language response
2. intent: detected response mode
3. products: ranked recommendations when applicable
4. cart_actions: optional action list interpreted by frontend cart UI

## Error Behavior

Typical API errors:

1. 400 for invalid payloads, including missing message and image
2. 422 for schema validation failures
3. 500 for unexpected backend errors

Frontend proxy behavior:

1. Frontend route forwards multipart requests to backend.
2. If backend is unreachable, proxy returns 502 with debug detail.

## Media Delivery Contract

Product images are served via:

1. /media/catalog/images/<file>.jpg

Production note:

1. Frontend resolves product image URLs to /media relative paths in deployed environments.

## Session Behavior

session_id usage:

1. Optional but recommended for multi-turn continuity.
2. Reuse the same value across related messages.

## cURL Smoke Test

Use this to verify end-to-end behavior quickly:

```bash
curl -sS -X POST http://localhost:8000/api/assistant/respond \
  -F "message=hello" \
  -F "session_id=smoke-test"
```

Expected:

1. HTTP 200 response
2. JSON body with response_text and intent
