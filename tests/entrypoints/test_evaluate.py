from assistant.entrypoints.evaluate import contains_expected


def test_an_answer_that_contains_the_expected_text_passes_whatever_the_case() -> None:
    assert contains_expected({"answer": "The ceiling is 25 €."}, {"expected": "25 €"}) is True
    assert contains_expected({"answer": "I DON'T KNOW."}, {"expected": "I don't know"}) is True


def test_an_answer_without_the_expected_text_fails() -> None:
    assert contains_expected({"answer": "Ten days."}, {"expected": "25 €"}) is False
