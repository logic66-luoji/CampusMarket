# 7. Challenges and Lessons Learned

This section documents the challenges the team actually encountered during
the development of CampusMarket, how they were resolved in the delivered
code, and what we learned from them. All examples reference the real
artifacts in the project repository.

## 7.1 Database Schema Evolution: From a Separate Orders Table to Transaction State on Products

The earliest version of the database (2026-11-18) used four tables. Purchases
were recorded in a dedicated `orders` table, and the anti-oversell guarantee
was the `UNIQUE` constraint on `orders.product_id`: the database itself made
it impossible to create two purchase records for the same product. When the
dataset was regenerated (2026-11-19), the team removed the `orders` table and
moved the transaction state directly onto the product row through three
columns: `buyer_id`, `status` (`available`/`sold`), and `finished_at`.

This change had consequences beyond the DDL. The anti-oversell mechanism had
to be re-founded: a `UNIQUE` constraint no longer protects the workflow,
because the guard must now be expressed as a conditional
`UPDATE ... WHERE status = 'available'`. The user-facing repository functions
changed signature and semantics (for example, `get_my_purchases` now queries
`products` instead of an orders table). The handover documents from the
early version — including the statement that "the `UNIQUE` constraint on
`orders.product_id` is the bottom line against overselling" — became
obsolete and had to be explicitly marked as historical so that nobody
re-introduced the old model.

**Lesson:** a schema change is not a file change; it invalidates every
mechanism, document, and test built on the old model. The version that
finally ships must be identifiable from the repository itself, which is why
the delivered project keeps a single authoritative database file and
regenerates `schema.sql` from it.

## 7.2 Transaction and Concurrency: Making a Conditional UPDATE the Only Writer of a Sale

After the schema change, oversell prevention depends on the atomicity of one
statement:

```sql
UPDATE products
SET buyer_id = ?, status = 'sold', finished_at = ?
WHERE product_id = ? AND status = 'available';
```

A subtle defect existed in the first version of this interface: it executed
the conditional UPDATE but returned "purchase successful" without checking
the affected-row count. If a competing request committed its own update
between the pre-check (`SELECT status ...`) and the UPDATE, the second
request would affect zero rows yet still report success — a sale that never
happened would be acknowledged to the user. The merged repository fixed this
by wrapping the update in an explicit transaction (`with conn:`) and
deciding the outcome from `cur.rowcount`: zero affected rows means another
buyer won, and the interface returns the "already purchased by someone else"
message.

SQLite's rollback journal serializes writers, so the loser's UPDATE waits
on the write lock and then re-evaluates the `WHERE` clause against the
committed state. Member C verified this behavior with a genuine
multi-threaded test (`tests/transactions/test_concurrency.py`): two threads
synchronized on a `threading.Barrier` call the real `buy_product()`
concurrently; across 10 recorded rounds the result was always exactly one
success and one failure, with the winner alternating between threads and the
loser consistently showing a longer wait time. The sequence tests additionally
confirmed that duplicate purchases, self-purchases, and purchases of
nonexistent products all fail without side effects.

**Lesson:** correctness under concurrency must be judged from the database's
own evidence (affected-row count, final row state), never from the code path
taken; and a concurrency test that only replays sequential calls proves
nothing — the barrier-synchronized threads were necessary to exercise the
race at all.

## 7.3 Separation of Application Layers: SQL Stays in the Repository

The early delivery contained a corrupted connection string
(`sqlite3.connect('database/campus_market.dbpython test_repo.py')`) that
silently created an empty database file and produced "no such table"
errors. This motivated the unified connection factory
(`database/connection.py`): one absolute, file-relative path, `PRAGMA
foreign_keys = ON` on every connection, and `sqlite3.Row` rows. The delivered
project enforces a strict three-layer split — Streamlit pages contain no SQL
and no connections, services contain validation and orchestration only, and
all SQL lives in `repositories/`. A repository-level audit (text search and
AST cross-checking of page-to-service references) confirmed the boundary
holds in the delivered code.

The split also shaped the interface contract. When the application needed new
queries, the pages could not simply add ad-hoc SQL; the data access layer
grew explicit functions instead. Two details are deliberate: sorting
expressions are chosen from a whitelist mapping (never string-concatenated
from user input), and product editing/deletion always includes `seller_id`
in the `WHERE` clause so ownership is enforced at the database level.

**Lesson:** layer separation is less about style than about where defects can
happen. Centralizing connections fixed a real bug class (path corruption,
forgotten foreign keys), and confining SQL made injection-safety review a
single-file task.

## 7.4 Data Integrity and Consistency: Constraints Must Be Turned On, Not Just Written

Three integrity-related incidents shaped the delivered design.

First, the early seed script had an indentation bug that left the `users`
table with a single row while products referenced seller IDs 1–100, so
foreign-key violations blocked every publish operation once foreign keys
were enabled; a remediation script had to backfill 99 accounts, and the
regenerated baseline (1,000 users) made the problem disappear.

Second, SQLite's `PRAGMA foreign_keys` is off by default **per connection**
and is not persisted in the file. Writing `FOREIGN KEY` clauses in the DDL
is therefore not enough; the connection factory enables the pragma on every
connection it returns, and the integration self-check asserts this. Member
C's tests inject invalid buyer/seller/category references and negative
prices into an isolated copy and verify each is rejected with an
`IntegrityError`.

Third, integrity extends to the workflow: a sold product's transaction
record must survive. The application blocks deletion of sold products (the
service layer raises a validation error and the page hides the delete
button), and the integrity tests check both directions of the status
invariant — every sold row has `buyer_id` and `finished_at`, every available
row keeps them NULL — against the full 10,000-row baseline and against a
post-purchase copy.

**Lesson:** declarative constraints only protect the system when the runtime
configuration (per-connection pragmas) and the business rules (what may be
deleted) are aligned with them — and when tests actually provoke the
violations instead of assuming they are impossible.

## 7.5 Team Collaboration and Integration: Merge, Do Not Replace

The integration step between Member A's database update and Member B's
application was the highest-risk moment of the project. A's update note said
to "directly replace the two same-named files." Doing so would have deleted
seven functions of B's repository layer (filter building, pagination,
counting, publish/edit/delete), immediately breaking the marketplace and
seller pages. B merged instead: A's new interfaces (`buy_product`,
`get_my_purchases`) were incorporated into the existing repository, adapted
to the unified connection factory and transaction boundary, and the new
database file was swapped in with a regenerated `schema.sql`.

The integration was then made verifiable rather than assumed: a read-only
self-check script (`check_interfaces.py`) asserts the model (three tables,
no `orders`), the fields, the data snapshot, foreign-key cleanliness, and
that A's performance script still runs. Handover documents recorded the data
snapshot (users/categories/products counts) and the do-not-run list (the
obsolete seed script would collide with the dataset if re-executed). A later
audit by Member C found one documentation/data mismatch — three products
purchased during a verification session were not restored, so the
available/sold split is 3,961/6,039 rather than the documented 3,964/6,036
while all totals agree — which was resolved by correcting the documented
figures rather than by touching the baseline database.

**Lesson:** when two members' deliverables overlap in one file, "replace" is
almost always the wrong verb; merge against an explicit interface contract,
and give the team a script that can re-verify the contract at any time.

## 7.6 Testing and Validation: Layered Evidence Instead of a Single Test

The project ended up with four complementary levels of verification, each
added by the member best placed to write it: A's index performance experiment
(with/without index timing and `EXPLAIN QUERY PLAN`), B's read-only
integration self-check of the model and interface contract, and Member C's
unittest suites — transaction semantics, multi-threaded oversell racing, and
integrity/constraint injection, all running on byte-copied database
instances with the repository connection factory redirected to the copy, so
the 10,000-product baseline is never written by a test. A final
service-level walkthrough replays the exact page call sequence from
publishing to purchase history.

Two practical lessons emerged from building the test environment. Replacing
the connection factory requires patching the name inside each repository
module (they import `get_connection` directly), not only the definition
module — the task looks symmetrical but is not. And test isolation needs a
tamper-evident guarantee: every test teardown re-hashes the baseline
database and fails if one byte changed, which turned "we were careful" into a
checkable property.

**Lesson:** each layer of the system needs its own falsifiable evidence;
when a layer cannot be exercised directly (in our case, Streamlit rendering
in a headless environment), state that limitation explicitly rather than
inferring the result from unrelated checks.
