from __future__ import annotations

from pathlib import Path
import statistics

from PIL import Image, ImageFilter, ImageStat


IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * p)
    return ordered[idx]


def main() -> None:
    img_dir = Path("backend/data/catalog/images")
    files = sorted([p for p in img_dir.glob("*") if p.suffix.lower() in IMG_EXTS])

    widths: list[int] = []
    heights: list[int] = []
    pixels: list[int] = []
    sizes: list[int] = []
    edge_variances: list[float] = []

    for path in files:
        try:
            with Image.open(path) as image:
                image = image.convert("RGB")
                width, height = image.size
                widths.append(width)
                heights.append(height)
                pixels.append(width * height)
                sizes.append(path.stat().st_size)

                edge = image.convert("L").filter(ImageFilter.FIND_EDGES)
                stats = ImageStat.Stat(edge)
                edge_variances.append(float(stats.var[0]))
        except Exception:
            continue

    if not widths:
        print("No readable images found.")
        return

    low_res_220 = sum(1 for px in pixels if px < 220 * 220)
    low_res_180 = sum(1 for px in pixels if px < 180 * 180)

    print(f"count={len(widths)}")
    print(
        f"resolution_min={min(widths)}x{min(heights)} resolution_max={max(widths)}x{max(heights)}"
    )
    print(
        f"resolution_median={int(statistics.median(widths))}x{int(statistics.median(heights))}"
    )
    print(
        "pixels_median={} pixels_p10={} pixels_p90={}".format(
            int(statistics.median(pixels)),
            int(percentile([float(v) for v in pixels], 0.10)),
            int(percentile([float(v) for v in pixels], 0.90)),
        )
    )
    print(
        "filesize_kb_median={:.1f} filesize_kb_p10={:.1f} filesize_kb_p90={:.1f}".format(
            statistics.median(sizes) / 1024,
            percentile([float(v) for v in sizes], 0.10) / 1024,
            percentile([float(v) for v in sizes], 0.90) / 1024,
        )
    )
    print(
        "edge_var_median={:.2f} edge_var_p10={:.2f} edge_var_p90={:.2f}".format(
            statistics.median(edge_variances),
            percentile(edge_variances, 0.10),
            percentile(edge_variances, 0.90),
        )
    )
    print(f"low_res_lt_220x220={low_res_220} low_res_lt_180x180={low_res_180}")


if __name__ == "__main__":
    main()
