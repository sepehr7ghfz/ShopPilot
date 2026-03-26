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
    <section className="product-results" aria-label="Recommended products">
      <header className="product-results-header">
        <h3>Recommended Products</h3>
      </header>
      <div className="product-grid" role="list">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </section>
  );
}
