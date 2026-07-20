package com.asef.fixture;

public final class Calculator {
    public int add(int left, int right) { return Math.addExact(left, right); }
    public int subtract(int left, int right) { return Math.subtractExact(left, right); }
    public int multiply(int left, int right) { return Math.multiplyExact(left, right); }
    public int divide(int left, int right) { return left / right; }
}
