import { NextRequest, NextResponse } from "next/server";

const DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:8000";
const backendBaseUrl = process.env.BACKEND_API_BASE_URL ?? DEFAULT_BACKEND_BASE_URL;
const backendAssistantUrl = `${backendBaseUrl}/api/assistant/respond`;
const backendTimeoutMs = Number(process.env.BACKEND_REQUEST_TIMEOUT_MS ?? "45000");

export async function POST(request: NextRequest): Promise<NextResponse> {
  const startedAt = Date.now();
  console.log("[frontend.proxy] incoming", {
    path: request.nextUrl.pathname,
    backendAssistantUrl,
  });

  try {
    const inboundFormData = await request.formData();
    const message = (inboundFormData.get("message") as string | null) ?? "";
    const hasImage = Boolean(inboundFormData.get("image"));
    const sessionId = (inboundFormData.get("session_id") as string | null) ?? "";

    console.log("[frontend.proxy] payload", {
      hasMessage: Boolean(message.trim()),
      hasImage,
      sessionId,
    });

    const outboundFormData = new FormData();
    if (message.trim()) {
      outboundFormData.append("message", message.trim());
    }

    const imageEntry = inboundFormData.get("image");
    if (imageEntry instanceof File) {
      outboundFormData.append("image", imageEntry, imageEntry.name || "upload.jpg");
    }

    if (sessionId.trim()) {
      outboundFormData.append("session_id", sessionId.trim());
    }

    const controller = new AbortController();
    const timeoutHandle = setTimeout(() => controller.abort(), backendTimeoutMs);

    let response: Response;
    try {
      response = await fetch(backendAssistantUrl, {
        method: "POST",
        body: outboundFormData,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeoutHandle);
    }

    const raw = await response.text();
    const elapsedMs = Date.now() - startedAt;
    console.log("[frontend.proxy] backend_response", {
      status: response.status,
      ok: response.ok,
      elapsedMs,
      preview: raw.slice(0, 220),
    });

    return new NextResponse(raw, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch (error) {
    const elapsedMs = Date.now() - startedAt;
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.log("[frontend.proxy] error", {
      elapsedMs,
      error: errorMessage,
      backendAssistantUrl,
    });

    return NextResponse.json(
      {
        detail: "Frontend proxy failed to reach backend assistant.",
        backend_url: backendAssistantUrl,
        error: errorMessage,
      },
      { status: 502 }
    );
  }
}
