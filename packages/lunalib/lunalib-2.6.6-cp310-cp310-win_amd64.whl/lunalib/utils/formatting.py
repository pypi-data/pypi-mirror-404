import os
from typing import Optional


def _format_number(value: float, decimals: int) -> str:
    fmt = f"{value:.{decimals}f}"
    if "." in fmt:
        fmt = fmt.rstrip("0").rstrip(".")
    return fmt


def _format_nonzero(value: float, min_decimals: int, max_decimals: int) -> str:
    decimals = min_decimals
    text = _format_number(value, decimals)
    if value == 0:
        return text
    while text in {"0", "-0"} and decimals < max_decimals:
        decimals += 1
        text = _format_number(value, decimals)
    return text


def format_amount(amount: Optional[float], unit: Optional[str] = None) -> str:
    """Format amount with human-friendly subunits (e.g., μLKC) for small values."""
    if amount is None:
        amount = 0.0

    try:
        value = float(amount)
    except Exception:
        value = 0.0

    base_unit = unit or os.getenv("LUNALIB_CURRENCY_UNIT", "LKC")
    decimals = int(os.getenv("LUNALIB_AMOUNT_DECIMALS", "8"))
    small_decimals = int(os.getenv("LUNALIB_AMOUNT_SMALL_DECIMALS", "4"))
    tiny_decimals = int(os.getenv("LUNALIB_AMOUNT_TINY_DECIMALS", "2"))
    max_tiny_decimals = int(os.getenv("LUNALIB_AMOUNT_MAX_DECIMALS", "12"))
    if decimals < 0:
        decimals = 0
    if small_decimals < 0:
        small_decimals = 0
    if tiny_decimals < 0:
        tiny_decimals = 0
    if max_tiny_decimals < small_decimals:
        max_tiny_decimals = small_decimals

    abs_value = abs(value)

    if abs_value >= 1:
        large_units = [
            (1e12, f"T{base_unit}"),
            (1e9, f"G{base_unit}"),
            (1e6, f"M{base_unit}"),
            (1e3, f"k{base_unit}"),
        ]
        for scale, suffix in large_units:
            if abs_value >= scale:
                return f"{_format_nonzero(value / scale, small_decimals, max_tiny_decimals)} {suffix}"
        return f"{_format_number(value, decimals)} {base_unit}"

    units = [
        (1e-3, f"m{base_unit}"),
        (1e-6, f"μ{base_unit}"),
        (1e-9, f"n{base_unit}"),
        (1e-12, f"p{base_unit}"),
    ]

    for scale, suffix in units:
        if abs_value >= scale:
            scaled = value / scale
            sub_decimals = max(small_decimals, tiny_decimals if abs(scaled) < 1 else small_decimals)
            return f"{_format_nonzero(scaled, sub_decimals, max_tiny_decimals)} {suffix}"

    if abs_value > 0:
        text = _format_nonzero(value, max(1, tiny_decimals), max_tiny_decimals)
        if text in {"0", "-0"}:
            return f"{value:.{max(1, tiny_decimals)}e} {base_unit}"
        return f"{text} {base_unit}"

    return f"{_format_number(value, small_decimals)} {base_unit}"
