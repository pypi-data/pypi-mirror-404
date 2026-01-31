from __future__ import annotations

import string
from typing import Mapping


def is_currency_code(code: str) -> bool:
    """
    Return True if `code` is a canonical XRPL currency code representation:
      - 3-character code (e.g. "USD"), OR
      - 160-bit currency code hex (40 hex chars).
    """
    if not isinstance(code, str):
        return False
    code = code.strip()
    if len(code) == 3:
        return True
    if len(code) != 40:
        return False
    try:
        bytes.fromhex(code)
    except ValueError:
        return False
    return True


def normalize_currency_code(code: str) -> str:
    """
    Normalize a canonical XRPL currency code representation:
      - trims whitespace
      - uppercases
      - validates shape (3-char or 40-hex)
    """
    if not isinstance(code, str):
        raise ValueError("Invalid currency code (expected string)")
    code = code.strip()
    if len(code) == 3:
        return code.upper()
    if len(code) == 40:
        try:
            bytes.fromhex(code)
        except ValueError as exc:
            raise ValueError("Invalid currency code (expected 40 hex chars)") from exc
        return code.upper()
    raise ValueError("Invalid currency code (expected 3 chars or 40 hex chars)")


def encode_currency_code_utf8_to_hex(symbol: str) -> str:
    """
    Encode a human-readable string into an XRPL 160-bit (20-byte) currency code hex.

    Rules:
    - UTF-8 encode `symbol`
    - must be <= 20 bytes
    - right-pad with null bytes to 20 bytes
    - return uppercase hex (40 chars)

    Example:
      "RLUSD" -> "524C555344000000000000000000000000000000"
    """
    if not isinstance(symbol, str):
        raise ValueError("Invalid symbol (expected string)")
    symbol = symbol.strip()
    if not symbol:
        raise ValueError("Invalid symbol (empty)")

    raw = symbol.encode("utf-8")
    if len(raw) > 20:
        raise ValueError("Symbol too long (max 20 bytes in UTF-8)")

    padded = raw.ljust(20, b"\x00")
    return padded.hex().upper()


def try_decode_currency_hex_to_utf8(code: str) -> str | None:
    """
    Best-effort decode of a 40-hex XRPL currency code into a printable UTF-8 string.

    - Strips trailing nulls (0x00) used for padding.
    - Returns None if decoding fails or the result is not printable.
    """
    if not isinstance(code, str):
        return None
    code = code.strip()
    if len(code) != 40:
        return None
    try:
        raw = bytes.fromhex(code)
    except ValueError:
        return None

    # Currency-code padding is trailing nulls.
    raw = raw.rstrip(b"\x00")
    if not raw:
        return None

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None

    if not text.isprintable():
        return None

    # Avoid returning a string that is only whitespace.
    if not text.strip():
        return None

    # Extra guard: ensure no control characters made it through.
    if any(ch not in string.printable for ch in text):
        return None

    return text


def display_currency_code(code: str) -> str:
    """
    Human-friendly display form:
      - 3-char code: returns uppercased code
      - 40-hex: returns decoded printable UTF-8 if possible, else the uppercase hex
    """
    code_norm = normalize_currency_code(code)
    if len(code_norm) == 3:
        return code_norm
    decoded = try_decode_currency_hex_to_utf8(code_norm)
    return decoded if decoded is not None else code_norm


def resolve_currency_code(
    value: str,
    *,
    aliases: Mapping[str, str] | None = None,
    allow_utf8_symbol: bool = False,
) -> str:
    """
    Resolve a user-supplied value into a canonical XRPL currency code (3-char or 40-hex).

    Resolution order:
    1) If `value` is already canonical: normalize and return it.
    2) If `aliases` is provided and contains a mapping: return normalized mapped value.
       (Lookup is performed on both the raw stripped value and its uppercased form.)
    3) If `allow_utf8_symbol=True`: encode value as UTF-8 padded 160-bit currency hex.
    4) Otherwise, raise ValueError.
    """
    if not isinstance(value, str):
        raise ValueError("Invalid currency value (expected string)")
    raw = value.strip()
    if not raw:
        raise ValueError("Invalid currency value (empty)")

    if is_currency_code(raw):
        return normalize_currency_code(raw)

    if aliases:
        if raw in aliases:
            return normalize_currency_code(aliases[raw])
        upper = raw.upper()
        if upper in aliases:
            return normalize_currency_code(aliases[upper])

    if allow_utf8_symbol:
        return encode_currency_code_utf8_to_hex(raw)

    raise ValueError("Unrecognized currency value (provide 3-char/40-hex, aliases, or allow_utf8_symbol=True)")

