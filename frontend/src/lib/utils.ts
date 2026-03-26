import { Product } from "@/lib/types";

const DEFAULT_MEDIA_BASE_URL = "/media";
const MEDIA_BASE_URL = process.env.NEXT_PUBLIC_MEDIA_BASE_URL ?? DEFAULT_MEDIA_BASE_URL;

export function formatPrice(price: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(price);
}

export function toDisplayCategory(category: string): string {
  if (!category) return "Unknown";
  return category
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function resolveProductImage(product: Product): string {
  if (product.image_url && /^https?:\/\//i.test(product.image_url)) {
    return product.image_url;
  }
  if (product.image_path && /^https?:\/\//i.test(product.image_path)) {
    return product.image_path;
  }

  if (product.image_path) {
    const normalizedPath = product.image_path.replace(/^\/+/, "");
    return `${MEDIA_BASE_URL}/${normalizedPath}`;
  }

  return "/placeholders/product.svg";
}

export function generateClientId(prefix: string): string {
  const timestamp = Date.now();
  const random = Math.random().toString(16).slice(2, 8);
  return `${prefix}-${timestamp}-${random}`;
}
