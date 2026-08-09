from _list_utils import split_list_items

def test_single_line_items():
    text = "- один\n- два\n- три"
    assert split_list_items(text) == ["- один", "- два", "- три"]


def test_wrapped_continuation_line_stays_in_same_item():
    text = (
        "- первый пункт с продолжением,\n"
        "  которое идёт на второй строке.\n"
        "- второй пункт."
    )
    items = split_list_items(text)
    assert len(items) == 2
    assert "которое идёт на второй строке." in items[0]
    assert items[1] == "- второй пункт."


def test_blank_line_ends_the_list():
    text = "- пункт один\n\nобычный текст после списка"
    items = split_list_items(text)
    assert items == ["- пункт один"]
