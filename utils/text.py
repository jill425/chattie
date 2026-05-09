import re

HAN_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def contains_chinese(text: str) -> bool:
    return bool(HAN_PATTERN.search(text))

