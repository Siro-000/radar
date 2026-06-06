"""
Dataset de testeo para Radar.

Contiene funciones organizadas en clusters temáticos.
Cada cluster incluye:
  - Función canónica (la "original")
  - Duplicados semánticos (misma lógica, distinta sintaxis)
  - Funciones distintas (para validar que NO se reportan como duplicados)

Convención de nombres en comentarios:
  [CANONICAL]  = función original del cluster
  [DUPLICATE]  = duplicado semántico (debería matchear con la canónica)
  [DISTINCT]   = función distinta (NO debería matchear)
"""

import re
import math
from datetime import datetime, timedelta
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 1 — Cálculo de descuentos / precios
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def apply_percentage_discount(price, pct):
    """Apply a percentage discount to a price."""
    if pct < 0 or pct > 100:
        raise ValueError("Discount must be between 0 and 100")
    discount_amount = price * pct / 100
    return price - discount_amount


# [DUPLICATE] — variables renombradas, misma lógica
def compute_sale_price(amount, discount_rate):
    """Compute the final sale price after applying a discount rate."""
    if discount_rate < 0 or discount_rate > 100:
        raise ValueError("Rate must be in 0-100 range")
    reduction = amount * discount_rate / 100
    return amount - reduction


# [DUPLICATE] — reestructurado con cálculo directo
def get_discounted_value(original, reduction):
    """Get the value after applying a percentage reduction."""
    if reduction < 0 or reduction > 100:
        raise ValueError("Invalid reduction percentage")
    factor = 1 - reduction / 100
    return original * factor


# [DISTINCT] — similar tema (porcentajes) pero calcula impuesto (suma en vez de resta)
def calculate_tax(amount, tax_rate):
    """Calculate the total amount including tax."""
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    tax = amount * tax_rate / 100
    return amount + tax


# [DISTINCT] — formatting, no cálculo
def format_price(amount, currency="USD"):
    """Format a numeric amount as a currency string."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 2 — Procesamiento de listas / filtrado
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def filter_even_numbers(numbers):
    """Filter a list to keep only even numbers."""
    result = []
    for num in numbers:
        if num % 2 == 0:
            result.append(num)
    return result


# [DUPLICATE] — list comprehension en vez de for loop
def get_even_values(data):
    """Return only the even values from a list of integers."""
    even_values = [x for x in data if x % 2 == 0]
    return even_values


# [DUPLICATE] — filter + lambda
def select_evens(input_list):
    """Select even numbers from the input list."""
    filtered = filter(lambda n: n % 2 == 0, input_list)
    result = list(filtered)
    return result


# [DISTINCT] — opuesto: filtra impares
def filter_odd_numbers(numbers):
    """Filter a list to keep only odd numbers."""
    result = []
    for num in numbers:
        if num % 2 != 0:
            result.append(num)
    return result


# [DISTINCT] — deduplicación, no filtrado por paridad
def remove_duplicates(items):
    """Remove duplicate items from a list preserving order."""
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


# [DISTINCT] — ordenamiento descendente
def sort_descending(values):
    """Sort a list of numbers in descending order."""
    sorted_values = sorted(values, reverse=True)
    return sorted_values


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 3 — Manipulación de strings
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def reverse_string(text):
    """Reverse the characters in a string."""
    reversed_text = text[::-1]
    return reversed_text


# [DUPLICATE] — usando reversed() y join
def flip_text(s):
    """Flip the text by reversing all characters."""
    characters = list(s)
    characters.reverse()
    return "".join(characters)


# [DUPLICATE] — loop manual construyendo el resultado
def invert_characters(input_str):
    """Invert the order of characters in a string."""
    output = ""
    for i in range(len(input_str) - 1, -1, -1):
        output += input_str[i]
    return output


# [DISTINCT] — capitaliza cada palabra
def capitalize_words(sentence):
    """Capitalize the first letter of each word in a sentence."""
    words = sentence.split()
    capitalized = [w.capitalize() for w in words]
    return " ".join(capitalized)


# [DISTINCT] — cuenta vocales
def count_vowels(text):
    """Count the number of vowels in a text string."""
    vowels = "aeiouAEIOU"
    count = 0
    for char in text:
        if char in vowels:
            count += 1
    return count


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 4 — Operaciones matemáticas
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def factorial(n):
    """Compute the factorial of n recursively."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


# [DUPLICATE] — iterativo en vez de recursivo
def compute_factorial(num):
    """Compute the factorial of a number iteratively."""
    if num < 0:
        raise ValueError("Cannot compute factorial of negative number")
    result = 1
    for i in range(2, num + 1):
        result *= i
    return result


# [DUPLICATE] — usando math.prod
def calc_factorial(x):
    """Calculate x! using a product of the range."""
    if x < 0:
        raise ValueError("Negative input not allowed")
    if x <= 1:
        return 1
    return math.prod(range(2, x + 1))


# [DISTINCT] — Fibonacci, no factorial
def fibonacci(n):
    """Return the n-th Fibonacci number."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


# [DISTINCT] — test de primalidad
def is_prime(n):
    """Check whether n is a prime number."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


# [DISTINCT] — potenciación manual
def power(base, exp):
    """Compute base raised to exp without using ** operator."""
    if exp < 0:
        raise ValueError("Negative exponents not supported")
    result = 1
    for _ in range(exp):
        result *= base
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 5 — Validación de datos
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def validate_email(email):
    """Validate an email address using a regex pattern."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not isinstance(email, str):
        raise TypeError("Email must be a string")
    return bool(re.match(pattern, email))


# [DUPLICATE] — mismo regex, variables distintas, estructura ligeramente diferente
def check_email_format(address):
    """Check whether an email address has a valid format."""
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not isinstance(address, str):
        raise TypeError("Expected a string input")
    match = re.match(regex, address)
    return match is not None


# [DUPLICATE] — implementación alternativa con split
def is_valid_email(mail_str):
    """Determine if the given string is a valid email address."""
    if not isinstance(mail_str, str):
        raise TypeError("Input must be a string")
    if "@" not in mail_str:
        return False
    local, _, domain = mail_str.rpartition("@")
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    return True


# [DISTINCT] — valida teléfono, no email
def validate_phone(phone):
    """Validate a phone number format (digits, dashes, optional +)."""
    if not isinstance(phone, str):
        raise TypeError("Phone must be a string")
    cleaned = phone.replace("-", "").replace(" ", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15


# [DISTINCT] — sanitización de input, no validación
def sanitize_input(text):
    """Sanitize user input by stripping dangerous characters."""
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    dangerous = ["<", ">", "&", '"', "'"]
    cleaned = text
    for char in dangerous:
        cleaned = cleaned.replace(char, "")
    return cleaned.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 6 — Operaciones con diccionarios
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def merge_dicts(dict_a, dict_b):
    """Merge two dictionaries; values from dict_b override dict_a."""
    merged = {}
    merged.update(dict_a)
    merged.update(dict_b)
    return merged


# [DUPLICATE] — usando operador | (Python 3.9+)
def combine_mappings(first, second):
    """Combine two mappings into one; second takes precedence."""
    result = {**first, **second}
    return result


# [DUPLICATE] — comprehension explícita
def join_dictionaries(d1, d2):
    """Join two dictionaries into a single dict."""
    combined = {k: v for k, v in d1.items()}
    for key, value in d2.items():
        combined[key] = value
    return combined


# [DISTINCT] — invierte key↔value
def invert_dict(d):
    """Invert a dictionary, swapping keys and values."""
    inverted = {}
    for key, value in d.items():
        inverted[value] = key
    return inverted


# [DISTINCT] — aplana diccionario anidado
def flatten_nested_dict(nested, parent_key="", sep="."):
    """Flatten a nested dictionary into a single-level dict with dotted keys."""
    items = {}
    for key, value in nested.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_nested_dict(value, new_key, sep))
        else:
            items[new_key] = value
    return items


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 7 — Lectura/escritura de archivos
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def read_lines(filepath):
    """Read a file and return its content as a list of lines."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    return lines


# [DUPLICATE] — usando pathlib
def load_file_lines(path):
    """Load file contents and split into lines using pathlib."""
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    return text.splitlines()


# [DUPLICATE] — usando readlines
def get_text_lines(filename):
    """Get all lines from a text file."""
    with open(filename, "r", encoding="utf-8") as handle:
        lines = handle.readlines()
    return [line.rstrip("\n") for line in lines]


# [DISTINCT] — escritura, no lectura
def write_lines(filepath, lines):
    """Write a list of strings to a file, one per line."""
    with open(filepath, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    return len(lines)


# [DISTINCT] — lee pero solo cuenta líneas
def count_lines_in_file(filepath):
    """Count the number of lines in a file."""
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 8 — Funciones de fecha/hora
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def parse_date(date_str):
    """Parse a date string in YYYY-MM-DD format into a datetime object."""
    parts = date_str.split("-")
    if len(parts) != 3:
        raise ValueError("Date must be in YYYY-MM-DD format")
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    return datetime(year, month, day)


# [DUPLICATE] — misma lógica, nombres distintos, usando strptime
def string_to_date(text):
    """Convert a date string to a datetime object."""
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    try:
        result = datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Expected format: YYYY-MM-DD")
    return result


# [DUPLICATE] — variante con try/except y fromisoformat
def convert_date_string(raw):
    """Convert a raw date string into a datetime, handling errors."""
    if not raw or not isinstance(raw, str):
        raise ValueError("Invalid date input")
    try:
        parsed = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        raise ValueError(f"Cannot parse date: {raw}")
    return parsed


# [DISTINCT] — inverso: date→string
def format_date(date_obj, fmt="%Y-%m-%d"):
    """Format a datetime object as a string."""
    if not isinstance(date_obj, datetime):
        raise TypeError("Expected a datetime object")
    formatted = date_obj.strftime(fmt)
    return formatted


# [DISTINCT] — calcula diferencia de días
def days_between(start, end):
    """Calculate the number of days between two dates."""
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        raise TypeError("Both arguments must be datetime objects")
    delta = abs((end - start).days)
    return delta


# ═══════════════════════════════════════════════════════════════════════════════
# CLUSTER 9 — Funciones de HTTP / requests
# ═══════════════════════════════════════════════════════════════════════════════

# [CANONICAL]
def fetch_json(url):
    """Fetch JSON data from a URL using urllib."""
    import urllib.request
    import json as json_mod
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        body = response.read().decode("utf-8")
    return json_mod.loads(body)


# [DUPLICATE] — misma lógica con variables distintas y headers
def get_api_response(endpoint):
    """Get a JSON response from an API endpoint."""
    import urllib.request
    import json as json_mod
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request) as resp:
        data = resp.read().decode("utf-8")
    return json_mod.loads(data)


# [DUPLICATE] — variante con manejo de errores
def download_json_data(api_url):
    """Download and parse JSON data from the given URL."""
    import urllib.request
    import json as json_mod
    try:
        req = urllib.request.Request(api_url)
        with urllib.request.urlopen(req) as response:
            raw = response.read().decode("utf-8")
        return json_mod.loads(raw)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {api_url}: {e}")


# [DISTINCT] — POST en vez de GET
def post_data(url, payload):
    """Send a POST request with JSON payload."""
    import urllib.request
    import json as json_mod
    data = json_mod.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as response:
        return json_mod.loads(response.read().decode("utf-8"))
