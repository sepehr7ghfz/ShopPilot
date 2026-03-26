import Image from "next/image";

import { Product } from "@/lib/types";
import { formatPrice, resolveProductImage, toDisplayCategory } from "@/lib/utils";

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps): JSX.Element {
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
        />
      </div>
      <div className="product-card-content">
        <div className="product-card-header">
          <h3>{product.name}</h3>
          <span>{formatPrice(product.price)}</span>
        </div>
        <p className="product-card-category">{toDisplayCategory(product.category)}</p>
        <p className="product-card-description">{product.description}</p>
        {product.reason ? <p className="product-card-reason">Why this match: {product.reason}</p> : null}
      </div>
    </article>
  );
}
