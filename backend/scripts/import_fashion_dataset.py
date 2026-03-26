from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any

from datasets import load_dataset


DATASET_NAME = "benitomartin/fashion-product-images-small-384x512"


def normalize_category(article_type: str, sub_category: str, master_category: str) -> str:
    text = " ".join([article_type, sub_category, master_category]).lower()

    if "hoodie" in text or "sweatshirt" in text:
        return "hoodie"
    if "t-shirt" in text or "tshirt" in text or "tee" in text or "top" in text:
        return "t-shirt"
    if "sneaker" in text or "shoe" in text or "trainer" in text:
        return "sneakers"
    if "jacket" in text or "coat" in text or "blazer" in text:
        return "jacket"
    if "backpack" in text or "bag" in text or "laptop bag" in text:
        return "backpack"

    fallback = (sub_category or master_category or "fashion").strip().lower()
    return re.sub(r"[^a-z0-9]+", "-", fallback).strip("-") or "fashion"


def tokenize(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2]


def build_tags(record: dict[str, Any]) -> list[str]:
    pool = [
        str(record.get("gender") or ""),
        str(record.get("masterCategory") or ""),
        str(record.get("subCategory") or ""),
        str(record.get("articleType") or ""),
        str(record.get("baseColour") or ""),
        str(record.get("season") or ""),
        str(record.get("usage") or ""),
        str(record.get("productDisplayName") or ""),
    ]

    tags: list[str] = []
    seen: set[str] = set()
    for item in pool:
        for token in tokenize(item):
            if token in seen:
                continue
            seen.add(token)
            tags.append(token)
            if len(tags) >= 12:
                return tags
    return tags


def build_price(category: str, source_id: str) -> float:
    seed = abs(hash(f"{category}:{source_id}")) % (10**6)
    rng = random.Random(seed)

    ranges: dict[str, tuple[int, int]] = {
        "t-shirt": (18, 54),
        "hoodie": (40, 110),
        "sneakers": (55, 180),
        "jacket": (65, 220),
        "backpack": (35, 140),
    }
    low, high = ranges.get(category, (20, 120))
    return round(rng.uniform(low, high), 2)


def build_description(record: dict[str, Any], category: str) -> str:
    display_name = str(record.get("productDisplayName") or "").strip()
    gender = str(record.get("gender") or "").strip()
    usage = str(record.get("usage") or "").strip()
    base_colour = str(record.get("baseColour") or "").strip()

    parts = [part for part in [gender, base_colour, category, usage] if part]
    descriptor = " ".join(parts).strip()

    if display_name:
        return f"{display_name}. {descriptor.capitalize()} item from curated fashion dataset.".strip()
    return f"{descriptor.capitalize()} item from curated fashion dataset.".strip()


def import_dataset(
    limit: int,
    output_catalog: Path,
    output_images_dir: Path,
    min_width: int,
    min_height: int,
) -> None:
    dataset = load_dataset(DATASET_NAME, split="train", streaming=True)

    output_images_dir.mkdir(parents=True, exist_ok=True)
    output_catalog.parent.mkdir(parents=True, exist_ok=True)

    imported: list[dict[str, Any]] = []
    for idx, row in enumerate(dataset):
        if len(imported) >= limit:
            break

        image = row.get("image")
        if image is None:
            continue

        width, height = image.size
        if width < min_width or height < min_height:
            continue

        source_id = str(row.get("id") or idx)
        article_type = str(row.get("articleType") or "")
        sub_category = str(row.get("subCategory") or "")
        master_category = str(row.get("masterCategory") or "")

        category = normalize_category(article_type, sub_category, master_category)
        product_id = f"hf-{source_id}"

        image_filename = f"{product_id}.jpg"
        image_path = output_images_dir / image_filename

        image.convert("RGB").save(image_path, format="JPEG", quality=90)

        name = str(row.get("productDisplayName") or article_type or sub_category or "Fashion Product").strip()
        record: dict[str, Any] = {
            "id": product_id,
            "name": name,
            "category": category,
            "description": build_description(row, category),
            "tags": build_tags(row),
            "price": build_price(category, source_id),
            "image_path": f"catalog/images/{image_filename}",
        }
        imported.append(record)

    if not imported:
        raise RuntimeError("No records were imported. Verify dataset availability and connectivity.")

    with output_catalog.open("w", encoding="utf-8") as handle:
        json.dump(imported, handle, ensure_ascii=True, indent=2)

    print(
        f"Imported {len(imported)} products into {output_catalog} and images into {output_images_dir}."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import fashion products with images for ShopPilot catalog.")
    parser.add_argument("--limit", type=int, default=600, help="Max number of products to import.")
    parser.add_argument(
        "--output-catalog",
        type=Path,
        default=Path("backend/data/catalog/products.json"),
        help="Path for generated products.json",
    )
    parser.add_argument(
        "--output-images-dir",
        type=Path,
        default=Path("backend/data/catalog/images"),
        help="Directory for downloaded product images.",
    )
    parser.add_argument("--min-width", type=int, default=300, help="Minimum accepted image width.")
    parser.add_argument("--min-height", type=int, default=300, help="Minimum accepted image height.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    import_dataset(
        limit=args.limit,
        output_catalog=args.output_catalog,
        output_images_dir=args.output_images_dir,
        min_width=args.min_width,
        min_height=args.min_height,
    )