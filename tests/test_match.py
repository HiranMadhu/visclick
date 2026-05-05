from visclick.match import best_box


def test_best_box_prefers_text_match() -> None:
    boxes = [
        (0, (0.0, 0.0, 10.0, 10.0), 0.9, "Cancel"),
        (0, (10.0, 10.0, 20.0, 20.0), 0.8, "Save"),
    ]
    r = best_box("click Save", boxes)
    assert r is not None
    _score, cls, _xy, _conf, text = r
    assert "Save" in text
    assert cls == 0


def test_best_box_refuses_when_label_not_present() -> None:
    """User asks for "click Save" but no box has Save text. Must NOT
    fall back to "the only button on screen" (Cancel)."""
    boxes = [
        (0, (0.0, 0.0, 10.0, 10.0), 0.9, "Cancel"),
        (1, (10.0, 10.0, 20.0, 20.0), 0.8, "Documents"),
        (1, (30.0, 30.0, 40.0, 40.0), 0.7, "Downloads"),
    ]
    r = best_box("click Save", boxes)
    assert r is None, "must refuse rather than mis-click"


def test_best_box_class_only_target_picks_class() -> None:
    """`click button` is a class-only target — pick the only button even
    if no OCR text matches the word 'button'."""
    boxes = [
        (1, (0.0, 0.0, 10.0, 10.0), 0.9, "Some label"),
        (0, (10.0, 10.0, 20.0, 20.0), 0.5, ""),  # button, no text
    ]
    r = best_box("click button", boxes)
    assert r is not None
    _score, cls, _xy, _conf, _text = r
    assert cls == 0
