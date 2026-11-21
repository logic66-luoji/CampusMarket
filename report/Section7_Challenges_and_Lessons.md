# 7. Challenges and Lessons Learned

**Schema evolution.** The first design recorded purchases in a separate `orders` table guarded by a `UNIQUE(product_id)` constraint. Regenerating the dataset without it forced us to re-found the anti-oversell guarantee as a conditional UPDATE — a schema change invalidates every mechanism and document built on the old model.

**Concurrency.** The first version of `buy_product()` reported success without checking the affected-row count, so a request that lost a race would still claim the purchase. The fix judges the outcome from `cur.rowcount` inside one transaction; correctness comes from the database's evidence, not the code path.

**Layer separation.** A corrupted connection string in an early delivery (which silently created an empty database) motivated the single connection factory and the rule that SQL lives only in repositories — centralizing connections eliminated a whole bug class and made SQL-safety review a one-file task.

**Constraints must be switched on.** SQLite keeps `PRAGMA foreign_keys` per connection, so declaring foreign keys is not enough; the factory enables the pragma everywhere and tests inject invalid references to prove rejection.

**Integration and testing.** When two members' files overlap, merging against an explicit interface contract beat "replacing the files". Every test runs on a byte-copied database with the repository connection factory redirected to the copy, and every teardown re-hashes the baseline — making "we were careful" a checkable property.
