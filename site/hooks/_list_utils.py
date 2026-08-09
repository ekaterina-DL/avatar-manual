import re

_ITEM_START_RE = re.compile(r'^-\s+')


def split_list_items(text):
    """Разбивает текст маркированного списка на пункты верхнего уровня. Строки-продолжения
    (без "- " в начале, идущие сразу за пунктом без пустой строки) остаются частью того же
    пункта. Пустая строка или конец текста — граница списка."""
    items = []
    current = []
    for line in text.split("\n"):
        if _ITEM_START_RE.match(line):
            if current:
                items.append("\n".join(current))
            current = [line]
        elif current and line.strip():
            current.append(line)
        else:
            if current:
                items.append("\n".join(current))
                current = []
    if current:
        items.append("\n".join(current))
    return items
