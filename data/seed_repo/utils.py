"""
Seed repo for Radar demo — contains planted duplicate pairs.

Each function here has a corresponding entry in data/heldout.json.
"""


def parse_iso_date(date_str):
    """Parse an ISO 8601 date string into a datetime object."""
    from datetime import datetime
    if not isinstance(date_str, str):
        raise TypeError(f"Expected str, got {type(date_str).__name__}")
    return datetime.fromisoformat(date_str)


def calculate_discount(price, percentage):
    """Return the discounted price after applying a percentage discount."""
    if percentage < 0 or percentage > 100:
        raise ValueError("Discount percentage must be between 0 and 100")
    discount_amount = price * percentage / 100
    return price - discount_amount


def paginate_results(items, page, page_size=10):
    """Slice a list to return one page of results (1-indexed)."""
    if page < 1:
        raise ValueError("Page number must be >= 1")
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def flatten_nested(nested_list):
    """Flatten a list of lists into a single flat list."""
    result = []
    for sublist in nested_list:
        for item in sublist:
            result.append(item)
    return result


def format_full_name(first, last, middle=None):
    """Format a person's full name, optionally including a middle name."""
    if middle:
        return f"{first} {middle} {last}"
    return f"{first} {last}"
