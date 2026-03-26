import { AssistantResponse, SendAssistantMessageInput } from "@/lib/types";

const DEFAULT_API_BASE_URL = "http://localhost:8000";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
const ASSISTANT_ENDPOINT = `${API_BASE_URL}/api/assistant/respond`;

export async function sendAssistantMessage(
  input: SendAssistantMessageInput
): Promise<AssistantResponse> {
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
    throw new Error(detail);
  }

  return (await response.json()) as AssistantResponse;
}
