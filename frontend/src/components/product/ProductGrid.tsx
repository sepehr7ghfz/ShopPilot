import { useState } from "react";

import { ProductCard } from "@/components/product/ProductCard";
import { Product } from "@/lib/types";

interface ProductGridProps {
  products: Product[];
}

function GridIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" className="product-view-icon">
      <rect x="3" y="3" width="7" height="7" rx="1.4" />
      <rect x="14" y="3" width="7" height="7" rx="1.4" />
      <rect x="3" y="14" width="7" height="7" rx="1.4" />
      <rect x="14" y="14" width="7" height="7" rx="1.4" />
    </svg>
  );
}

function ListIcon(): JSX.Element {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" className="product-view-icon">
      <rect x="3" y="4" width="3" height="3" rx="0.8" />
      <rect x="8" y="4" width="13" height="3" rx="0.8" />
      <rect x="3" y="10.5" width="3" height="3" rx="0.8" />
      <rect x="8" y="10.5" width="13" height="3" rx="0.8" />
      <rect x="3" y="17" width="3" height="3" rx="0.8" />
      <rect x="8" y="17" width="13" height="3" rx="0.8" />
    </svg>
  );
}

export function ProductGrid({ products }: ProductGridProps): JSX.Element {
  const [viewMode, setViewMode] = useState<"grid" | "list">("list");

  if (!products.length) {
    return <></>;
  }

  return (
    <section className="product-results" aria-label="Recommended products">
      <header className="product-results-header">
        <h3>Recommended Products</h3>
        <div className="product-view-switch" role="tablist" aria-label="Product view mode">
          <button
            type="button"
            className={viewMode === "grid" ? "is-active" : ""}
            onClick={() => setViewMode("grid")}
            aria-pressed={viewMode === "grid"}
            title="Grid view"
          >
            <GridIcon />
            <span className="product-view-label">Grid</span>
          </button>
          <button
            type="button"
            className={viewMode === "list" ? "is-active" : ""}
            onClick={() => setViewMode("list")}
            aria-pressed={viewMode === "list"}
            title="List view"
          >
            <ListIcon />
            <span className="product-view-label">List</span>
          </button>
        </div>
      </header>
      <div className={`product-grid ${viewMode === "list" ? "product-grid-list" : ""}`} role="list">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </section>
  );
}
