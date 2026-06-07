package com.acme.util;

/** Canonical date helpers. */
public class DateUtils {

    public static boolean isLeapYear(int year) {
        if (year % 400 == 0) {
            return true;
        }
        if (year % 100 == 0) {
            return false;
        }
        return year % 4 == 0;
    }

    public static int daysInMonth(int month, int year) {
        int[] days = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
        if (month == 2 && isLeapYear(year)) {
            return 29;
        }
        return days[month - 1];
    }

    public static String formatIso(int year, int month, int day) {
        String mm = month < 10 ? "0" + month : String.valueOf(month);
        String dd = day < 10 ? "0" + day : String.valueOf(day);
        return year + "-" + mm + "-" + dd;
    }
}
