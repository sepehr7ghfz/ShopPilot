from __future__ import annotations

import statistics
from datasets import load_dataset
from PIL import ImageFilter, ImageStat


CANDIDATES = [
    "ashraq/fashion-product-images-small",
    "benitomartin/fashion-product-images-small-384x512",
    "benitomartin/fashion-product-images-small-900x1200",
    "Ahmad1931259/fashion-product-images",
]


def main() -> None:
    for ds_name in CANDIDATES:
        print(f"\n=== {ds_name} ===")
        try:
            ds = load_dataset(ds_name, split="train[:120]")
        except Exception as exc:
            print(f"load_failed {str(exc)[:220]}")
            continue

        widths: list[int] = []
        heights: list[int] = []
        pixels: list[int] = []
        edge_variances: list[float] = []

        for row in ds:
            image = row.get("image")
            if image is None:
                continue
            width, height = image.size
            widths.append(width)
            heights.append(height)
            pixels.append(width * height)
            edge_variances.append(
                float(ImageStat.Stat(image.convert("L").filter(ImageFilter.FIND_EDGES)).var[0])
            )

        if not widths:
            print("no_images")
            continue

        print(f"count {len(widths)}")
        print(f"median_res {int(statistics.median(widths))}x{int(statistics.median(heights))}")
        print(f"min_res {min(widths)}x{min(heights)} max_res {max(widths)}x{max(heights)}")
        print(f"median_pixels {int(statistics.median(pixels))}")
        print(f"edge_var_median {statistics.median(edge_variances):.2f}")


if __name__ == "__main__":
    main()
