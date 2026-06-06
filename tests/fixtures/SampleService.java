public class SampleService {

    public double calculateTax(double price, double rate) {
        double amount = price * rate / 100;
        double result = price + amount;
        return result;
    }

    public String greet(String name) {
        String message = "Hello, " + name + "!";
        String upper = message.toUpperCase();
        return upper;
    }

    public static int add(int a, int b) {
        int sum = a + b;
        return sum;
    }

    public SampleService() {
        int x = 0;
        int y = 1;
        int z = x + y;
    }

    public void noop() {
    }
}
