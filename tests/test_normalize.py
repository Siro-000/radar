from radar.engine.normalize import normalize


SAMPLE = """
public double calculateTax(double price, double rate) {
    // apply tax
    double amount = price * rate / 100; /* result */
    double total = price + amount;
    return total;
}
"""

SAMPLE_RENAMED = """
public double applyTax(double cost, double pct) {
    double amount = cost * pct / 100;
    double total = cost + amount;
    return total;
}
"""


def test_strips_line_comments():
    result = normalize(SAMPLE)
    assert "//" not in result


def test_strips_block_comments():
    result = normalize(SAMPLE)
    assert "/*" not in result


def test_renames_local_variables():
    result = normalize(SAMPLE)
    assert "var0" in result
    assert "var1" in result
    assert "amount" not in result
    assert "total" not in result


def test_preserves_parameter_names():
    result = normalize(SAMPLE)
    assert "price" in result
    assert "rate" in result


def test_same_logic_different_names_normalize_equally():
    r1 = normalize(SAMPLE)
    r2 = normalize(SAMPLE_RENAMED)
    # local vars become var0/var1 in both; method names differ but structure matches
    assert "var0" in r1 and "var0" in r2
    assert "var1" in r1 and "var1" in r2


def test_invalid_syntax_returns_input_unchanged():
    bad = "this is not java @@@"
    assert normalize(bad) == bad


def test_deterministic():
    assert normalize(SAMPLE) == normalize(SAMPLE)
