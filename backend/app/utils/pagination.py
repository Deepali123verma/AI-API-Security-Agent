from math import ceil


def normalize_pagination(page: int, page_size: int) -> tuple[int, int]:
    safe_page = max(page, 1)
    safe_page_size = min(max(page_size, 1), 100)
    return safe_page, safe_page_size


def pagination_meta(total: int, page: int, page_size: int) -> dict[str, int]:
    total_pages = ceil(total / page_size) if total else 0
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }


def offset_for(page: int, page_size: int) -> int:
    return (page - 1) * page_size
