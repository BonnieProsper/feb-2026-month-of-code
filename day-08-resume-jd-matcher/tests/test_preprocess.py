from src.preprocess import preprocess_text


def test_basic_normalization():
    text = "Python, Docker & SQL."
    result = preprocess_text(text)

    assert "python" in result.tokens
    assert "docker" in result.tokens
    assert "sql" in result.tokens


def test_idempotency():
    text = "Built APIs in Python."
    first = preprocess_text(text)
    second = preprocess_text(" ".join(first.tokens))

    assert second.tokens == first.tokens


def test_empty_input():
    result = preprocess_text("")
    assert result.tokens == []
