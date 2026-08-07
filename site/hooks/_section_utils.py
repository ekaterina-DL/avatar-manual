import re

_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*$')


def _find_heading(lines, heading):
    for i, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match and match.group(2) == heading:
            return i, len(match.group(1))
    return None, None


def extract_section(text, heading):
    """Тело раздела с заданным заголовком (без строки заголовка), до следующего заголовка
    того же или более высокого уровня, либо до конца текста. None, если заголовок не найден."""
    lines = text.split("\n")
    start, level = _find_heading(lines, heading)
    if start is None:
        return None
    body_lines = []
    for line in lines[start + 1:]:
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) <= level:
            break
        body_lines.append(line)
    return "\n".join(body_lines)


def strip_section(text, heading):
    """Текст без раздела heading (включая строку заголовка). Без изменений, если не найден."""
    lines = text.split("\n")
    start, level = _find_heading(lines, heading)
    if start is None:
        return text
    end = start + 1
    for line in lines[start + 1:]:
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) <= level:
            break
        end += 1
    return "\n".join(lines[:start] + lines[end:])
