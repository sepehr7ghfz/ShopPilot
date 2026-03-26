from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PriceConstraints:
    min_price: float | None = None
    max_price: float | None = None

    def applies(self) -> bool:
        return self.min_price is not None or self.max_price is not None


def parse_price_constraints(text: str | None) -> PriceConstraints:
    if not text:
        return PriceConstraints()

    normalized = text.lower().replace(",", "")

    range_match = re.search(
        r"(?:between|from)\s*\$?\s*(\d+(?:\.\d+)?)\s*(?:and|to|-)\s*\$?\s*(\d+(?:\.\d+)?)",
        normalized,
    )
    if range_match:
        first = float(range_match.group(1))
        second = float(range_match.group(2))
        return PriceConstraints(min_price=min(first, second), max_price=max(first, second))

    max_match = re.search(
        r"(?:below|under|less than|cheaper than|at most|up to|<=)\s*\$?\s*(\d+(?:\.\d+)?)",
        normalized,
    )
    min_match = re.search(
        r"(?:above|over|more than|greater than|at least|minimum|>=)\s*\$?\s*(\d+(?:\.\d+)?)",
        normalized,
    )

    max_price = float(max_match.group(1)) if max_match else None
    min_price = float(min_match.group(1)) if min_match else None

    return PriceConstraints(min_price=min_price, max_price=max_price)


def in_price_range(price: float, constraints: PriceConstraints) -> bool:
    if constraints.min_price is not None and price < constraints.min_price:
        return False
    if constraints.max_price is not None and price > constraints.max_price:
        return False
    return True
