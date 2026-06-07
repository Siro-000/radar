package com.acme.collection;

import java.util.ArrayList;
import java.util.List;

/** Canonical collection helpers. */
public class ListUtils {

    public static double average(List<Integer> nums) {
        int total = 0;
        for (int n : nums) {
            total = total + n;
        }
        return (double) total / nums.size();
    }

    public static int findMax(List<Integer> nums) {
        int best = nums.get(0);
        for (int n : nums) {
            if (n > best) {
                best = n;
            }
        }
        return best;
    }

    public static List<Integer> filterEven(List<Integer> nums) {
        List<Integer> out = new ArrayList<>();
        for (int n : nums) {
            if (n % 2 == 0) {
                out.add(n);
            }
        }
        return out;
    }

    public static boolean contains(int[] arr, int target) {
        for (int i = 0; i < arr.length; i++) {
            if (arr[i] == target) {
                return true;
            }
        }
        return false;
    }
}
