package com.acme.legacy;

/**
 * Legacy grab-bag. Each method here is a PLANTED semantic duplicate of a
 * canonical helper elsewhere in the repo (same logic, different name/syntax).
 * Ground truth for the dedup demo:
 *   greatestCommonDivisor  ~ MathUtils.gcd
 *   reverseText            ~ StringUtils.reverse
 *   checkPrime             ~ MathUtils.isPrime
 *   addUp                  ~ MathUtils.sumArray
 *   addTax                 ~ TaxCalculator.calculateTax
 *   isLeap                 ~ DateUtils.isLeapYear
 *   linearSearch           ~ ListUtils.contains
 *   palindromeCheck        ~ StringUtils.isPalindrome
 */
public class Helpers {

    // dup of MathUtils.gcd (recursive instead of iterative)
    public static int greatestCommonDivisor(int x, int y) {
        if (y == 0) {
            return x;
        }
        return greatestCommonDivisor(y, x % y);
    }

    // dup of StringUtils.reverse (char array instead of StringBuilder)
    public static String reverseText(String text) {
        char[] chars = text.toCharArray();
        String out = "";
        for (int i = chars.length - 1; i >= 0; i--) {
            out = out + chars[i];
        }
        return out;
    }

    // dup of MathUtils.isPrime (different bound expression)
    public static boolean checkPrime(int num) {
        if (num <= 1) {
            return false;
        }
        for (int d = 2; d <= num / d; d++) {
            if (num % d == 0) {
                return false;
            }
        }
        return true;
    }

    // dup of MathUtils.sumArray (while loop instead of for-each)
    public static int addUp(int[] values) {
        int acc = 0;
        int i = 0;
        while (i < values.length) {
            acc += values[i];
            i++;
        }
        return acc;
    }

    // dup of TaxCalculator.calculateTax (different variable names)
    public static double addTax(double amount, double percent) {
        double extra = amount * percent / 100;
        double total = amount + extra;
        return total;
    }

    // dup of DateUtils.isLeapYear (boolean vars instead of branches)
    public static boolean isLeap(int yr) {
        boolean byFour = yr % 4 == 0;
        boolean byHundred = yr % 100 == 0;
        boolean byFourHundred = yr % 400 == 0;
        return (byFour && !byHundred) || byFourHundred;
    }

    // dup of ListUtils.contains (enhanced-for instead of index loop)
    public static boolean linearSearch(int[] data, int key) {
        for (int element : data) {
            if (element == key) {
                return true;
            }
        }
        return false;
    }

    // dup of StringUtils.isPalindrome (reverse-and-compare approach)
    public static boolean palindromeCheck(String word) {
        StringBuilder rev = new StringBuilder(word).reverse();
        return word.equals(rev.toString());
    }
}
