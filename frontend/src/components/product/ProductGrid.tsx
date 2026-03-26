import { ProductCard } from "@/components/product/ProductCard";
import { Product } from "@/lib/types";

interface ProductGridProps {
  products: Product[];
}

export function ProductGrid({ products }: ProductGridProps): JSX.Element {
  if (!products.length) {
    return <></>;
  }

  return (
    <div className="product-grid" role="list">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
