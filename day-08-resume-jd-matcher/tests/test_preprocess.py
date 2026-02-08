from src.preprocess import preprocess_text


def test_basic_normalization():
    text = "Python, Docker & SQL."
    tokens = preprocess_text(text)

    assert "python" in tokens
    assert "docker" in tokens
    assert "sql" in tokens


def test_idempotency():
    text = "Built APIs in Python."
    tokens = preprocess_text(text)

    assert preprocess_text(" ".join(tokens)) == tokens


def test_empty_input():
    assert preprocess_text("") == []
