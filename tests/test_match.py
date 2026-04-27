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
