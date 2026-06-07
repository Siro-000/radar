# Acme Commerce Platform — development conventions

Package all new classes under `src/com/acme/commerce/` following the existing domain structure.
Reuse shared utilities from `com.acme.commerce.util` (MoneyUtils, DateUtils, StringUtils, MathUtils) instead of reimplementing them.
