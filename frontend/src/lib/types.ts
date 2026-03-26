export type AssistantIntent =
  | "general_chat"
  | "text_recommendation"
  | "image_search"
  | "hybrid_search";

export interface Product {
  id: string;
  name: string;
  category: string;
  price: number;
  description: string;
  image_path?: string;
  image_url?: string;
  reason?: string;
}

export interface AssistantResponse {
  response_text: string;
  intent: AssistantIntent;
  products: Product[];
  cart_actions?: CartAction[];
}

export interface CartAction {
  action: "add" | "remove" | "clear";
  product_ids: string[];
  note?: string;
}

export interface SendAssistantMessageInput {
  message?: string;
  imageFile?: File | null;
  sessionId?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  imagePreviewUrl?: string;
  products?: Product[];
  intent?: AssistantIntent;
  isError?: boolean;
}
