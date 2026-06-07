#!/usr/bin/env python3
"""Generate a realistic Java e-commerce repo for testing the Radar MCP.

Plants 3 semantic duplicates with completely different vocabulary — not
greppable by keyword, but Radar matches them by logic.

Usage:
    python3 demo/gen_test_repo.py                    # creates ../prueba_demo
    python3 demo/gen_test_repo.py /path/to/output    # custom path
    python3 demo/gen_test_repo.py --filler 15        # more filler classes
"""

from __future__ import annotations

import argparse
import shutil
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Real classes — canonical implementations
# ---------------------------------------------------------------------------

CLASSES: dict[str, str] = {
    "com/acme/commerce/product/ProductService.java": """\
package com.acme.commerce.product;

import java.util.List;
import java.util.Optional;

/** CRUD operations for the product catalogue. */
public class ProductService {

    public static Optional<String> findById(List<String[]> catalogue, String id) {
        return catalogue.stream()
                .filter(p -> p[0].equals(id))
                .map(p -> p[1])
                .findFirst();
    }

    public static List<String[]> findByCategory(List<String[]> catalogue, String category) {
        return catalogue.stream()
                .filter(p -> p[2].equalsIgnoreCase(category))
                .toList();
    }
}
""",
    "com/acme/commerce/product/ProductValidator.java": """\
package com.acme.commerce.product;

/** Validates product data before persistence. */
public class ProductValidator {

    public static boolean isValidSku(String sku) {
        return sku != null && sku.matches("^[A-Z]{2,4}-[0-9]{4,8}$");
    }

    public static boolean isValidPrice(double price) {
        return price > 0 && price < 1_000_000;
    }

    public static boolean isValidName(String name) {
        return name != null && name.length() >= 2 && name.length() <= 120;
    }
}
""",
    "com/acme/commerce/order/CartService.java": """\
package com.acme.commerce.order;

import java.util.HashMap;
import java.util.Map;

/** Manages the shopping cart lifecycle. */
public class CartService {

    public static Map<String, Integer> addItem(Map<String, Integer> cart, String sku, int qty) {
        cart.merge(sku, qty, Integer::sum);
        return cart;
    }

    public static Map<String, Integer> removeItem(Map<String, Integer> cart, String sku) {
        cart.remove(sku);
        return cart;
    }

    public static int itemCount(Map<String, Integer> cart) {
        return cart.values().stream().mapToInt(Integer::intValue).sum();
    }
}
""",
    "com/acme/commerce/order/OrderCalculator.java": """\
package com.acme.commerce.order;

import java.util.List;

/** Computes order-level totals. */
public class OrderCalculator {

    public static double subtotal(List<Double> unitPrices, List<Integer> quantities) {
        double total = 0;
        for (int i = 0; i < unitPrices.size(); i++) {
            total += unitPrices.get(i) * quantities.get(i);
        }
        return total;
    }

    public static double grandTotal(double subtotal, double taxAmount, double shippingCost) {
        return subtotal + taxAmount + shippingCost;
    }
}
""",
    "com/acme/commerce/customer/CustomerValidator.java": """\
package com.acme.commerce.customer;

/** Validates customer profile fields. */
public class CustomerValidator {

    public static boolean isValidEmail(String email) {
        return email != null && email.matches("^[\\\\w.+-]+@[\\\\w-]+\\\\.[\\\\w.]+$");
    }

    public static boolean isValidPhone(String phone) {
        return phone != null && phone.matches("^\\\\+?[0-9]{7,15}$");
    }

    public static boolean isValidPostalCode(String code, String countryCode) {
        if ("US".equals(countryCode)) return code.matches("^[0-9]{5}(-[0-9]{4})?$");
        if ("AR".equals(countryCode)) return code.matches("^[A-Z][0-9]{4}[A-Z]{3}$");
        return code != null && code.length() >= 3;
    }
}
""",
    "com/acme/commerce/customer/CustomerService.java": """\
package com.acme.commerce.customer;

/** Core customer account operations. */
public class CustomerService {

    public static String buildDisplayName(String firstName, String lastName) {
        if (firstName == null || firstName.isBlank()) return lastName;
        if (lastName == null || lastName.isBlank()) return firstName;
        return firstName.trim() + " " + lastName.trim();
    }

    public static boolean isEligibleForLoyalty(int totalOrders, double lifetimeSpend) {
        return totalOrders >= 5 || lifetimeSpend >= 500.0;
    }
}
""",
    "com/acme/commerce/payment/TaxCalculator.java": """\
package com.acme.commerce.payment;

/** Computes tax-inclusive prices. */
public class TaxCalculator {

    /** Returns the price after adding a percentage tax.
     *  e.g. price=100, rate=21 -> 121.0 */
    public static double calculateTax(double price, double rate) {
        return price + price * rate / 100;
    }

    public static double taxAmount(double price, double rate) {
        return price * rate / 100;
    }
}
""",
    "com/acme/commerce/payment/PricingEngine.java": """\
package com.acme.commerce.payment;

/** Core pricing transformations. */
public class PricingEngine {

    /** Applies a percentage discount. e.g. price=200, pct=10 -> 180.0 */
    public static double applyDiscount(double price, double percentage) {
        return price * (1.0 - percentage / 100.0);
    }

    public static double applyMarkup(double cost, double marginPct) {
        return cost / (1.0 - marginPct / 100.0);
    }
}
""",
    "com/acme/commerce/shipping/ShippingCalculator.java": """\
package com.acme.commerce.shipping;

/** Calculates shipping costs based on weight and destination. */
public class ShippingCalculator {

    public static double baseRate(double weightKg, double ratePerKg) {
        return weightKg * ratePerKg;
    }

    public static double withInsurance(double shippingCost, double declaredValue) {
        return shippingCost + declaredValue * 0.01;
    }

    public static boolean qualifiesForFreeShipping(double orderTotal, double threshold) {
        return orderTotal >= threshold;
    }
}
""",
    "com/acme/commerce/inventory/StockService.java": """\
package com.acme.commerce.inventory;

import java.util.Map;

/** Manages stock availability and reservations. */
public class StockService {

    public static boolean isAvailable(Map<String, Integer> stock, String sku, int qty) {
        return stock.getOrDefault(sku, 0) >= qty;
    }

    public static void reserve(Map<String, Integer> stock, String sku, int qty) {
        if (!isAvailable(stock, sku, qty)) {
            throw new IllegalStateException("Insufficient stock for SKU: " + sku);
        }
        stock.put(sku, stock.get(sku) - qty);
    }
}
""",
    "com/acme/commerce/promotion/CouponService.java": """\
package com.acme.commerce.promotion;

/** Validates and applies promotional coupons. */
public class CouponService {

    public static boolean isValidCode(String code) {
        return code != null && code.length() >= 6 && code.matches("[A-Z0-9]+");
    }

    public static double redemptionValue(double orderTotal, double faceValue) {
        return Math.min(faceValue, orderTotal);
    }
}
""",
    "com/acme/commerce/util/DateUtils.java": """\
package com.acme.commerce.util;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/** Date parsing and formatting helpers. */
public class DateUtils {

    public static LocalDate parseIsoDate(String raw) {
        return LocalDate.parse(raw);
    }

    public static String format(LocalDate date, String pattern) {
        return date.format(DateTimeFormatter.ofPattern(pattern));
    }

    public static boolean isFuture(LocalDate date) {
        return date.isAfter(LocalDate.now());
    }
}
""",
    "com/acme/commerce/util/MoneyUtils.java": """\
package com.acme.commerce.util;

/** Currency formatting and rounding helpers. */
public class MoneyUtils {

    public static String format(double amount, String currencySymbol) {
        return currencySymbol + String.format("%.2f", amount);
    }

    public static double round(double amount) {
        return Math.round(amount * 100.0) / 100.0;
    }

    public static boolean isPositive(double amount) {
        return amount > 0;
    }
}
""",
    "com/acme/commerce/util/StringUtils.java": """\
package com.acme.commerce.util;

/** General-purpose string helpers. */
public class StringUtils {

    public static String slugify(String text) {
        return text.trim().toLowerCase().replaceAll("[^a-z0-9]+", "-");
    }

    public static String truncate(String text, int maxLen) {
        if (text == null || text.length() <= maxLen) return text;
        return text.substring(0, maxLen - 3) + "...";
    }

    public static String capitalize(String word) {
        if (word == null || word.isEmpty()) return word;
        return Character.toUpperCase(word.charAt(0)) + word.substring(1).toLowerCase();
    }
}
""",
    "com/acme/commerce/util/MathUtils.java": """\
package com.acme.commerce.util;

/** Numeric helpers used across the platform. */
public class MathUtils {

    public static double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }

    public static double roundTo(double value, int decimals) {
        double scale = Math.pow(10, decimals);
        return Math.round(value * scale) / scale;
    }

    public static double percentage(double part, double total) {
        if (total == 0) return 0;
        return (part / total) * 100;
    }
}
""",
}

# ---------------------------------------------------------------------------
# Hidden semantic duplicates — same logic, completely different vocabulary
# ---------------------------------------------------------------------------

HIDDEN: dict[str, str] = {
    # DUPLICATE 1: same as calculateTax(price, rate) -> price + price*rate/100
    # Domain: vendor marketplace fees. Close enough vocabulary that the agent
    # must recognise it as a duplicate (saleAmount + feeRate -> commission math).
    "com/acme/commerce/marketplace/VendorFeeEngine.java": """\
package com.acme.commerce.marketplace;

/** Computes the total amount a vendor receives including platform fee. */
public class VendorFeeEngine {

    public static double applyVendorFee(double saleAmount, double feeRate) {
        return saleAmount + saleAmount * feeRate / 100;
    }
}
""",
    # DUPLICATE 2: same as applyDiscount(price, pct) -> price * (1 - pct/100)
    # Domain: shipping rebates. Zero overlap with discount/price/percentage.
    "com/acme/commerce/shipping/ShippingAdjuster.java": """\
package com.acme.commerce.shipping;

/** Adjusts quoted shipping costs with carrier rebates. */
public class ShippingAdjuster {

    public static double netAfterRebate(double base, double rebatePct) {
        double multiplier = 1.0 - rebatePct / 100.0;
        return base * multiplier;
    }
}
""",
    # DUPLICATE 3: same as parseIsoDate(String) -> LocalDate.parse(raw)
    # Domain: report parsing. Zero overlap with date/parse/iso vocabulary.
    "com/acme/commerce/report/ReportParser.java": """\
package com.acme.commerce.report;

import java.time.LocalDate;

/** Extracts typed fields from raw report export strings. */
public class ReportParser {

    public static LocalDate extractDate(String input) {
        return LocalDate.parse(input);
    }

    public static double extractAmount(String input) {
        return Double.parseDouble(input.replaceAll("[^0-9.]", ""));
    }
}
""",
}

# ---------------------------------------------------------------------------
# Filler classes — realistic but not duplicates of anything
# ---------------------------------------------------------------------------

_FILLER_TEMPLATES = [
    ("analytics", "EventTracker",     "trackPageView",   "trackAddToCart"),
    ("analytics", "ConversionMetrics","conversionRate",  "bounceRate"),
    ("notification","EmailDispatcher","sendOrderConfirm","sendShipmentAlert"),
    ("notification","SmsGateway",     "sendOtp",         "sendDeliveryUpdate"),
    ("report",    "SalesAggregator",  "dailyRevenue",    "topProducts"),
    ("report",    "ExportBuilder",    "toCsvRow",        "toJsonRow"),
    ("promotion", "LoyaltyEngine",    "earnPoints",      "redeemPoints"),
    ("promotion", "CampaignService",  "isActive",        "applyCampaign"),
    ("product",   "ReviewService",    "averageRating",   "reviewCount"),
    ("customer",  "AddressService",   "formatAddress",   "validateCountry"),
    ("payment",   "RefundProcessor",  "calculateRefund", "issueCredit"),
    ("payment",   "CardValidator",    "luhnCheck",       "detectNetwork"),
    ("order",     "InvoiceService",   "generateNumber",  "formatLineItem"),
    ("inventory", "WarehouseManager", "locateBin",       "transferStock"),
    ("shipping",  "DeliveryEstimator","estimateDays",    "selectCarrier"),
    ("util",      "CacheUtils",       "buildKey",        "invalidate"),
]


def filler_class(i: int) -> tuple[str, str]:
    tpl = _FILLER_TEMPLATES[i % len(_FILLER_TEMPLATES)]
    domain, cls, m1, m2 = tpl
    suffix = i // len(_FILLER_TEMPLATES)
    cls_name = cls if suffix == 0 else f"{cls}V{suffix}"
    pkg = f"com.acme.commerce.{domain}"
    path = f"com/acme/commerce/{domain}/{cls_name}.java"
    source = textwrap.dedent(f"""\
        package {pkg};

        public class {cls_name} {{

            public static String {m1}(String input) {{
                if (input == null || input.isBlank()) return "";
                return input.trim();
            }}

            public static double {m2}(double[] values) {{
                double sum = 0;
                for (double v : values) sum += v;
                return sum / Math.max(1, values.length);
            }}
        }}
        """)
    return path, source


# ---------------------------------------------------------------------------
# Repo-level files
# ---------------------------------------------------------------------------

REPO_README = """\
# Acme Commerce Platform

Java backend for the Acme e-commerce platform.

## Overview

Handles the full commerce lifecycle: product catalog, shopping cart, order processing,
payment, shipping, and customer management.

## Package structure

| Package | Responsibility |
|---|---|
| `com.acme.commerce.product` | Product catalog, search, and validation |
| `com.acme.commerce.order` | Cart management and order processing |
| `com.acme.commerce.customer` | Customer profiles and address handling |
| `com.acme.commerce.payment` | Pricing, tax calculation, and payment |
| `com.acme.commerce.shipping` | Shipping costs and delivery estimates |
| `com.acme.commerce.billing` | Invoicing and regulatory levies |
| `com.acme.commerce.inventory` | Stock management |
| `com.acme.commerce.promotion` | Discounts, coupons, and campaigns |
| `com.acme.commerce.report` | Sales reporting and data export |
| `com.acme.commerce.util` | Shared utilities |

## Build

```bash
mvn clean package
```

## Running tests

```bash
mvn test
```

## Requirements

- Java 17+
- Maven 3.8+
"""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DIRS = [SCRIPT_DIR.parent.parent / "prueba_demo"]


def generate(out: Path, filler: int) -> None:
    if out.exists():
        shutil.rmtree(out)

    src = out / "src"
    all_classes = {**CLASSES, **HIDDEN}
    for i in range(filler):
        path, source = filler_class(i)
        all_classes[path] = source

    for rel_path, source in all_classes.items():
        target = src / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)

    (out / "README.md").write_text(REPO_README)

    real = len(CLASSES)
    hidden = len(HIDDEN)
    total = real + hidden + filler

    print(f"\nGenerated repo at: {out}")
    print(f"  {real} real classes  |  {hidden} hidden duplicates  |  {filler} filler  =  {total} total\n")
    print("Hidden semantic duplicates planted:")
    print("  VendorFeeEngine.applyVendorFee  <- same logic as TaxCalculator.calculateTax")
    print("  ShippingAdjuster.netAfterRebate <- same logic as PricingEngine.applyDiscount")
    print("  ReportParser.extractDate        <- same logic as DateUtils.parseIsoDate")
    print()
    print("Test commands:")
    print(f"  uv run radar index --repo {out} --index-path {out}/.radar-index")
    print(f"  uv run radar query --index-path {out}/.radar-index \\")
    print("    'public static double calculateCommission(double saleAmount, double commissionRate) {")
    print("        return saleAmount + saleAmount * commissionRate / 100; }'")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a realistic Java test repo for Radar.")
    parser.add_argument("output_dirs", nargs="*", help="Output directories (default: ../prueba_demo)")
    parser.add_argument("--filler", type=int, default=8, help="Filler classes (default 8)")
    args = parser.parse_args()

    targets = [Path(d).resolve() for d in args.output_dirs] if args.output_dirs else DEFAULT_DIRS
    for out in targets:
        generate(out, args.filler)


if __name__ == "__main__":
    main()
