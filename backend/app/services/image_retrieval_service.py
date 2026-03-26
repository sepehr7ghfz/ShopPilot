from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.schemas.product import CatalogProduct
from app.services.catalog_service import CatalogService
from app.utils.image_io import load_image_from_bytes, load_image_from_path, resolve_catalog_image_path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImageRetrievalResult:
    product: CatalogProduct
    score: float
    reason: str | None


class ImageRetrievalService:
    """CLIP-based visual similarity retrieval over local catalog images."""

    def __init__(
        self,
        catalog_service: CatalogService,
        model_name: str = "openai/clip-vit-base-patch32",
        min_similarity: float = 0.2,
    ) -> None:
        self.catalog_service = catalog_service
        self.model_name = model_name
        self.min_similarity = min_similarity

        self._catalog_root = Path(__file__).resolve().parents[2] / "data" / "catalog"
        self._data_root = self._catalog_root.parent

        self._torch: Any | None = None
        self._model: Any | None = None
        self._processor: Any | None = None
        self._indexed_items: list[tuple[CatalogProduct, Any]] = []
        self._is_index_ready = False

    def retrieve_from_bytes(self, image_bytes: bytes, limit: int = 5) -> list[ImageRetrievalResult]:
        if not image_bytes:
            raise ValueError("No image bytes were provided.")

        query_image = load_image_from_bytes(image_bytes)
        query_vector = self._embed_image(query_image)
        self._ensure_catalog_index()

        if not self._indexed_items:
            return []

        scored: list[ImageRetrievalResult] = []
        for product, catalog_vector in self._indexed_items:
            score = float(self._torch.dot(query_vector, catalog_vector).item())
            scored.append(
                ImageRetrievalResult(
                    product=product,
                    score=score,
                    reason=f"visual similarity score: {score:.2f}",
                )
            )

        scored.sort(key=lambda item: (-item.score, item.product.price, item.product.id))
        return scored[:limit]

    def _ensure_catalog_index(self) -> None:
        if self._is_index_ready:
            return

        self._load_model()
        indexed_items: list[tuple[CatalogProduct, Any]] = []

        for product in self.catalog_service.get_all_products():
            image_path = resolve_catalog_image_path(
                image_path=product.image_path,
                data_root=self._data_root,
                catalog_root=self._catalog_root,
            )

            if not image_path.exists():
                logger.warning("catalog.image_missing product_id=%s path=%s", product.id, image_path)
                continue

            try:
                image = load_image_from_path(image_path)
                vector = self._embed_image(image)
                indexed_items.append((product, vector))
            except ValueError:
                logger.warning("catalog.image_unreadable product_id=%s path=%s", product.id, image_path)

        self._indexed_items = indexed_items
        self._is_index_ready = True

    def _load_model(self) -> None:
        if self._model is not None and self._processor is not None and self._torch is not None:
            return

        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor
        except ImportError as exc:
            raise RuntimeError(
                "Image retrieval dependencies are missing. Install: pip install torch transformers pillow"
            ) from exc

        device = "cpu"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"

        processor = CLIPProcessor.from_pretrained(self.model_name)
        model = CLIPModel.from_pretrained(self.model_name)
        model.eval()
        model.to(device)

        self._torch = torch
        self._processor = processor
        self._model = model
        self._device = device

    def _embed_image(self, image: Any) -> Any:
        self._load_model()
        assert self._processor is not None
        assert self._model is not None
        assert self._torch is not None

        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {key: value.to(self._device) for key, value in inputs.items()}

        with self._torch.no_grad():
            features = self._model.get_image_features(**inputs)
            if hasattr(features, "image_embeds"):
                features = features.image_embeds
            elif hasattr(features, "pooler_output"):
                features = features.pooler_output
            if not hasattr(features, "norm"):
                raise RuntimeError("CLIP image embedding output format is not supported.")
            features = features / features.norm(dim=-1, keepdim=True)

        return features[0].detach().to("cpu")
