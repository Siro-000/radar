package com.acme.validation;

/** Canonical validation helpers. */
public class ValidationUtils {

    public static boolean isValidEmail(String email) {
        if (email == null) {
            return false;
        }
        int at = email.indexOf('@');
        int dot = email.lastIndexOf('.');
        return at > 0 && dot > at + 1 && dot < email.length() - 1;
    }

    public static boolean isBlank(String s) {
        if (s == null) {
            return true;
        }
        return s.trim().isEmpty();
    }

    public static int clamp(int value, int lo, int hi) {
        if (value < lo) {
            return lo;
        }
        if (value > hi) {
            return hi;
        }
        return value;
    }
}
