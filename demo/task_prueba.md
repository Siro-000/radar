Add sales commission tracking to the platform.

Create `src/com/acme/commerce/sales/CommissionCalculator.java` with a public class
`CommissionCalculator` that exposes:

    public static double calculateCommission(double saleAmount, double commissionRate)

A sales agent earns a percentage on top of every sale. The method returns the total
amount — sale price plus the agent's commission. Follow the existing package conventions
and reuse utilities where appropriate. Write the file; do not run anything.
