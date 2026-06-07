Add invoice support to this codebase.

Create `src/com/acme/billing/Invoice.java` with a public class `Invoice` that
exposes a public static method:

    double totalWithTax(double price, double rate)

It must return the final price including sales tax, where the tax is
`price * rate / 100`. Follow the repo's existing conventions and reuse existing
utilities where appropriate. Write the file; do not run anything.
