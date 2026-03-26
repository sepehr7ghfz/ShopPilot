import { AssistantResponse, SendAssistantMessageInput } from "@/lib/types";

const DEFAULT_ASSISTANT_ENDPOINT = "/api/assistant/respond";
const ASSISTANT_ENDPOINT = process.env.NEXT_PUBLIC_API_BASE_URL
  ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/assistant/respond`
  : DEFAULT_ASSISTANT_ENDPOINT;

export async function sendAssistantMessage(
  input: SendAssistantMessageInput
): Promise<AssistantResponse> {
  const startedAt = Date.now();
  console.log("[frontend.api] sendAssistantMessage:start", {
    hasMessage: Boolean(input.message?.trim()),
    hasImage: Boolean(input.imageFile),
    sessionId: input.sessionId,
  });

  const formData = new FormData();

  const trimmedMessage = input.message?.trim();
  if (trimmedMessage) {
    formData.append("message", trimmedMessage);
  }

  if (input.imageFile) {
    formData.append("image", input.imageFile);
  }

  if (input.sessionId) {
    formData.append("session_id", input.sessionId);
  }

  const response = await fetch(ASSISTANT_ENDPOINT, {
    method: "POST",
    body: formData,
  });

  console.log("[frontend.api] sendAssistantMessage:http", {
    status: response.status,
    ok: response.ok,
    elapsedMs: Date.now() - startedAt,
  });

  if (!response.ok) {
    let detail = "Failed to reach assistant.";
    try {
      const errorPayload = (await response.json()) as { detail?: string };
      if (errorPayload?.detail) {
        detail = errorPayload.detail;
      }
    } catch {
      // Keep default detail if response body is not JSON.
    }
    console.log("[frontend.api] sendAssistantMessage:error", { detail });
    throw new Error(detail);
  }
  const payload = (await response.json()) as AssistantResponse;
  console.log("[frontend.api] sendAssistantMessage:success", {
    intent: payload.intent,
    products: payload.products?.length ?? 0,
    elapsedMs: Date.now() - startedAt,
  });

  return payload;
}
