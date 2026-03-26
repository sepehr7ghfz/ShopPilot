import Image from "next/image";

import { Product } from "@/lib/types";
import { formatPrice, resolveProductImage, toDisplayCategory } from "@/lib/utils";

interface ProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
}

export function ProductCard({ product, onAddToCart }: ProductCardProps): JSX.Element {
  const imageSrc = resolveProductImage(product);

  return (
    <article className="product-card">
      <div className="product-card-image-wrap">
        <Image
          src={imageSrc}
          alt={product.name}
          className="product-card-image"
          fill
          sizes="(max-width: 768px) 100vw, 300px"
          unoptimized
        />
      </div>
      <div className="product-card-content">
        <div className="product-card-kicker">ShopPilot Pick</div>
        <div className="product-card-header">
          <h3>{product.name}</h3>
          <div className="product-card-header-actions">
            <button
              type="button"
              className="product-card-add-btn"
              onClick={() => onAddToCart?.(product)}
              title="Add to cart"
              aria-label={`Add ${product.name} to cart`}
            >
              🛒
            </button>
            <span>{formatPrice(product.price)}</span>
          </div>
        </div>
        <p className="product-card-category">{toDisplayCategory(product.category)}</p>
        <p className="product-card-description">{product.description}</p>
      </div>
      {product.reason ? (
        <footer className="product-card-footer">
          <details className="product-card-reason-details">
            <summary>Why this match</summary>
            <p className="product-card-reason">{product.reason}</p>
          </details>
        </footer>
      ) : null}
    </article>
  );
}
