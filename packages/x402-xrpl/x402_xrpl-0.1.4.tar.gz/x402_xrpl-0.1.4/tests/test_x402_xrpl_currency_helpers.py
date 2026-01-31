import pytest

from x402_xrpl.xrpl_currency import (
    display_currency_code,
    encode_currency_code_utf8_to_hex,
    is_currency_code,
    normalize_currency_code,
    resolve_currency_code,
    try_decode_currency_hex_to_utf8,
)


RLUSD_HEX = "524C555344000000000000000000000000000000"


def test_encode_currency_code_utf8_to_hex_rlusd():
    assert encode_currency_code_utf8_to_hex("RLUSD") == RLUSD_HEX


def test_try_decode_currency_hex_to_utf8_rlusd():
    assert try_decode_currency_hex_to_utf8(RLUSD_HEX) == "RLUSD"


def test_display_currency_code_prefers_decoded_text_for_hex():
    assert display_currency_code(RLUSD_HEX) == "RLUSD"


def test_display_currency_code_3char_uppercases():
    assert display_currency_code("usd") == "USD"


def test_is_currency_code_accepts_3char_and_40hex():
    assert is_currency_code("USD") is True
    assert is_currency_code(RLUSD_HEX) is True
    assert is_currency_code("RLUSD") is False
    assert is_currency_code("ZZ") is False


def test_normalize_currency_code_uppercases_and_validates():
    assert normalize_currency_code("usd") == "USD"
    assert normalize_currency_code(RLUSD_HEX.lower()) == RLUSD_HEX
    with pytest.raises(ValueError):
        normalize_currency_code("RLUSD")
    with pytest.raises(ValueError):
        normalize_currency_code("G" * 40)  # not hex


def test_resolve_currency_code_accepts_canonical_inputs():
    assert resolve_currency_code("usd") == "USD"
    assert resolve_currency_code(RLUSD_HEX.lower()) == RLUSD_HEX


def test_resolve_currency_code_with_aliases():
    aliases = {"RLUSD": RLUSD_HEX}
    assert resolve_currency_code("RLUSD", aliases=aliases) == RLUSD_HEX
    assert resolve_currency_code("rlusd", aliases=aliases) == RLUSD_HEX


def test_resolve_currency_code_allow_utf8_symbol():
    assert resolve_currency_code("RLUSD", allow_utf8_symbol=True) == RLUSD_HEX


def test_resolve_currency_code_rejects_unknown_without_flags():
    with pytest.raises(ValueError):
        resolve_currency_code("RLUSD")

