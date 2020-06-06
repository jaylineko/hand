import re

_blocks = []

with open("emoji.txt", mode="r", encoding="utf-8") as f:
    for line in f:
        match = re.match(r"([0-9A-F]+)(?:..([0-9A-F]+))?", line)
        if not match:
            continue

        start = int(match.group(1), 16)
        end = int(match.group(2) or match.group(1), 16)

        _blocks.append((start, end))


def _in_emoji_block(char):
    for block_start, block_end in _blocks:
        if block_start <= ord(char) <= block_end:
            return True

    return False


def is_emoji(str):
    for char in str:
        if not _in_emoji_block(char):
            return False
    return True
