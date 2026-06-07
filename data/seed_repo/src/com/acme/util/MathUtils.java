package com.acme.util;

/** Canonical numeric helpers. */
public class MathUtils {

    public static int gcd(int a, int b) {
        while (b != 0) {
            int temp = b;
            b = a % b;
            a = temp;
        }
        return a;
    }

    public static long factorial(int n) {
        long result = 1;
        for (int i = 2; i <= n; i++) {
            result = result * i;
        }
        return result;
    }

    public static boolean isPrime(int n) {
        if (n < 2) {
            return false;
        }
        for (int i = 2; i * i <= n; i++) {
            if (n % i == 0) {
                return false;
            }
        }
        return true;
    }

    public static int maxOf(int[] arr) {
        int best = arr[0];
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] > best) {
                best = arr[i];
            }
        }
        return best;
    }

    public static int sumArray(int[] arr) {
        int total = 0;
        for (int value : arr) {
            total = total + value;
        }
        return total;
    }

    public static long power(int base, int exp) {
        long result = 1;
        for (int i = 0; i < exp; i++) {
            result = result * base;
        }
        return result;
    }
}
