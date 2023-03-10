from typing import Generator, TypeVar

T = TypeVar("T")


def chunk_list(l: list[T], chunk_size: int) -> Generator[list[T], list[T], None]:
    """Break a list into smaller list of size `chunk_size`"""
    for i in range(0, len(l), chunk_size):
        yield l[i : i + chunk_size]


def consolidate_message_parts(parts: list[str], sep: str = "\n", max_length: int = 2000) -> list[str]:
    """
    Combines multiple parts of a message into the largest message possible without exceeding the max length

    Args:
        parts (list[str]): list of parts (if a single part it longer than the max length, it will be broken in two)
        sep (str): the separator to combine parts
        max_length (int): the max length of a single combined part

    Returns:
        consolidated_parts (list[str]): a list of consolidated parts
    """

    consolidated_parts: list[str] = []

    consolidated_part_len = 0
    components: list[str] = []
    for part in parts:
        # split up large parts
        if len(part) > max_length:
            sub_part = part
            while len(sub_part) > max_length:
                consolidated_parts.append(sub_part[:max_length])
                sub_part = sub_part[max_length:]

            consolidated_parts.append(sub_part)
            continue

        # build consolidated_part and track length
        components.append(part)
        consolidated_part_len += len(part)

        # combine components into a consolidated part
        if consolidated_part_len + (len(sep) * (len(components) - 1)) > max_length:
            consolidated_part = sep.join(components[:-1])
            consolidated_parts.append(consolidated_part)

            components = []
            consolidated_part_len = 0

    # add remaining parts
    if components:
        consolidated_parts.append(sep.join(components))

    return consolidated_parts
