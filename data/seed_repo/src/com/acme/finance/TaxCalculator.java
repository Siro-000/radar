package com.acme.finance;

/** Canonical finance helpers. */
public class TaxCalculator {

    public static double calculateTax(double price, double rate) {
        double amount = price * rate / 100;
        double result = price + amount;
        return result;
    }

    public static double applyDiscount(double price, double pct) {
        double off = price * pct / 100;
        double result = price - off;
        return result;
    }

    public static double compoundInterest(double principal, double rate, int years) {
        double amount = principal;
        for (int i = 0; i < years; i++) {
            amount = amount + amount * rate / 100;
        }
        return amount;
    }
}
