# CampusMarket — A Campus Second-hand Trading Platform

**Database Systems · Track 1 — Database Application Development**

# 1. Group Information

| Member | Name | Student ID | Undergraduate Major |
| --- | --- | --- | --- |
| Member A | Wang Fangcheng（王方成） | 72640065 | Financial Mathematics |
| Member B | Cai Haoneng（蔡浩能） | 72640692 | Economics |
| Member C | Li Jijia（李积佳） | 72640201 | Communication Engineering |

# 2. Contribution Statement

- **Member A（Wang Fangcheng）** designed the relational schema and DDL; built the SQLite database and the synthetic dataset (1,000 users / 5 categories / 10,000 products with campus-oriented Chinese descriptions); implemented the purchase data-access interfaces (`buy_product`, `get_my_purchases`) and the index performance experiment script (`performance_test.py`); supplied the database artifacts and measurements underlying Sections 5–6.
- **Member B（Cai Haoneng）** built the unified connection factory (`database/connection.py`), the repository layer (filtering, whitelist sorting, pagination, publish/edit/delete) and service layer, the four Streamlit pages and the purchase workflow integration, and the read-only self-check script (`check_interfaces.py`); drafted the application-design material in Sections 3–4.
- **Member C（Li Jijia）** audited the delivered codebase and database; designed and ran the transaction, concurrency, integrity and functional test suites on isolated database copies; verified the application live in a browser; drew the report figures; consolidated this report; prepared the video script and demonstration checklist.

# 3. Project Overview

**Problem statement.** Campus second-hand trading typically happens through informal chat groups, where product information is unstructured, searches are manual, and completed transactions leave no reliable record. Information about users, categories, products, and purchases must stay mutually consistent — in particular, the same item must never be sold twice, and sellers must not be able to alter or erase completed sales.

**Application goals.** CampusMarket provides a centralized web platform that (1) organizes users, categories, and products in a relational database with primary keys, foreign keys, and CHECK constraints; (2) supports keyword search, category and price-range filtering, whitelist sorting, and pagination over available products; (3) lets users publish, edit, and delete their own listings while preserving sold-product records; (4) records purchases as exactly-once transactions; and (5) demonstrates a maintainable three-layer separation of presentation, business logic, and data access.

**Target users.** University students buying and selling second-hand goods on campus. For demonstration purposes the current scope uses predefined test accounts switched in the sidebar instead of a registration/password system; payment, logistics, and reviews are out of scope.

# 4. Technical Design

| Technology | Role |
| --- | --- |
| Python 3 (stdlib `sqlite3`, `unittest`, `threading`) | Application language, database driver, test framework |
| Streamlit ≥ 1.31 | Web front end: entry page + four business pages, session state |
| SQLite (`campus_market.db`) | Embedded relational database, no server deployment |
| pandas / Faker | Supporting dependencies for the data-preparation workflow (archived `seed.py`) |

The application follows a three-layer architecture. The **presentation layer** (Streamlit pages) renders UI and holds the current test account in session state, but contains no SQL and no database connections. The **business logic layer** (`product_service.py`, `user_service.py`) validates input, assembles search parameters, and orchestrates operations. The **data access layer** (`repositories/`) is the only place where SQL is written: all statements are parameterized, sort expressions come from a fixed whitelist, and ownership checks are embedded in UPDATE/DELETE `WHERE` clauses. Every connection is obtained from a single factory (`database/connection.py`) that uses an absolute file path, enables `PRAGMA foreign_keys = ON` per connection, and returns `sqlite3.Row` rows. Figure 1 shows the layers and their dependencies.

![](report/figures/Figure1_CampusMarket_Architecture.png)

# 5. Database Design

## 5.1 ER Diagram

The schema has three entities. A user publishes many products (`seller_id`, ON DELETE CASCADE); a category groups many products (`category_id`, ON DELETE RESTRICT); and a purchase does **not** create a new entity — it is recorded by updating the product row's `buyer_id` (ON DELETE SET NULL), `status`, and `finished_at`. Figure 2 shows the model with crow's-foot cardinalities.

![](report/figures/Figure2_CampusMarket_ER_Diagram.png)

## 5.2 Schema

```sql
CREATE TABLE users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email         VARCHAR(100) UNIQUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(50) NOT NULL UNIQUE
);
CREATE TABLE products (
    product_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id   INTEGER NOT NULL,
    buyer_id    INTEGER DEFAULT NULL,
    category_id INTEGER NOT NULL,
    title       VARCHAR(100) NOT NULL,
    description TEXT,
    price       DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    status      VARCHAR(20) DEFAULT 'available'
                CHECK (status IN ('available', 'sold')),
    image_url   VARCHAR(255),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP DEFAULT NULL,
    FOREIGN KEY (seller_id)   REFERENCES users(user_id)          ON DELETE CASCADE,
    FOREIGN KEY (buyer_id)    REFERENCES users(user_id)          ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT
);
```

## 5.3 Normalization

The schema is in **third normal form (3NF)**. All columns are atomic (1NF); every non-key attribute depends on the whole single-column surrogate key (2NF); and no non-key attribute depends on another non-key attribute (3NF) — for example, the category *name* is stored only in `categories` and joined at query time rather than duplicated in `products`. Purchase facts (`buyer_id`, `status`, `finished_at`) depend on `product_id` alone and are stored on the product row instead of a separate `orders` table, a deliberate design decision that keeps each sale tied to exactly one row (Section 5.4).

## 5.4 Transaction Design

A purchase is one conditional UPDATE executed in a single transaction; the affected-row count decides the outcome (Figure 3). Self-purchases and sold products are rejected by pre-checks, and any competing buyer that commits first makes the loser's UPDATE match zero rows.

![](report/figures/Figure3_Buyer_Transaction_Workflow.png)

## 5.5 Indexing Strategy

| Index | Columns | Supports |
| --- | --- | --- |
| `idx_products_category_status` | (category_id, status) | Marketplace filtering `WHERE status='available' [AND category_id=?]` — column order matches the filter, enabling seeks and covering-index scans |
| `idx_products_buyer` | (buyer_id) | Purchase history `WHERE buyer_id=? AND status='sold'` |

## 5.6 Sample Queries

```sql
-- Q1 Marketplace listing (composite index seek; plan: SEARCH USING INDEX)
SELECT p.*, c.name AS category_name
FROM products p JOIN categories c ON c.category_id = p.category_id
WHERE p.status = 'available' AND p.title LIKE ?  -- plus optional price/category
ORDER BY p.created_at DESC LIMIT ? OFFSET ?;

-- Q2 Purchase (exactly-once guarantee; plan: single-row conditional UPDATE)
UPDATE products SET buyer_id = ?, status = 'sold', finished_at = ?
WHERE product_id = ? AND status = 'available';

-- Q3 Purchase history (buyer index; join restores category names)
SELECT p.*, c.name AS category_name
FROM products p JOIN categories c ON c.category_id = p.category_id
WHERE p.buyer_id = ? AND p.status = 'sold'
ORDER BY p.finished_at DESC;
```

# 6. Evaluation and Results

All measurements were executed on 2026-11-21 against the delivered database (Windows 10, Python 3.10.0, SQLite 3.35.5; products = 10,000: 3,961 available / 6,039 sold), opened read-only; a 110,000-row scaled copy was used for the trend experiment and deleted afterwards.

**Query efficiency.** `EXPLAIN QUERY PLAN` confirms the marketplace query is executed as `SEARCH … USING INDEX idx_products_category_status`, while disabling the index (`category_id + 0 = 1`) falls back to `SCAN TABLE`. Averaged over 500 warm executions, the index reduces pure traversal cost (`SELECT COUNT(*)`, fully covered by the index) by **8.2×** at 10,000 rows and **12.8×** at 110,000 rows:

| Table size | Indexed (covering seek) | Forced scan | Ratio |
| ---: | ---: | ---: | ---: |
| 10,000 rows | 0.038 ms | 0.313 ms | 8.2× |
| 110,000 rows | 0.235 ms | 3.021 ms | 12.8× |

For the full row-returning query, end-to-end latency is dominated by materialising the 791 matching rows (1.52 ms indexed vs 1.72 ms scanned at 10k rows, 1.1×) — the index keeps traversal cost proportional to the result set rather than the table, an advantage that grows with data volume.

**Integrity, concurrency, and usability.** Thirteen automated tests (`tests/`) all pass: the ten consistency rules (foreign-key validity, sold/available invariants, price/status domains) hold on all 10,000 baseline rows with zero violations, and CHECK/foreign-key violations are provably rejected with `IntegrityError`; in ten barrier-synchronized two-thread purchase races on the real `buy_product()`, every round ended with exactly one winner and one loser, the row always `sold` with the winner's `buyer_id` and a non-NULL `finished_at`; and the four Streamlit pages plus the complete purchase workflow were verified live in a browser (screenshots in `presentation/screenshots/`).

# 7. Challenges and Lessons Learned

**Schema evolution.** The first design recorded purchases in a separate `orders` table guarded by a `UNIQUE(product_id)` constraint. Regenerating the dataset without it forced us to re-found the anti-oversell guarantee as a conditional UPDATE — a schema change invalidates every mechanism and document built on the old model.

**Concurrency.** The first version of `buy_product()` reported success without checking the affected-row count, so a request that lost a race would still claim the purchase. The fix judges the outcome from `cur.rowcount` inside one transaction; correctness comes from the database's evidence, not the code path.

**Layer separation.** A corrupted connection string in an early delivery (which silently created an empty database) motivated the single connection factory and the rule that SQL lives only in repositories — centralizing connections eliminated a whole bug class and made SQL-safety review a one-file task.

**Constraints must be switched on.** SQLite keeps `PRAGMA foreign_keys` per connection, so declaring foreign keys is not enough; the factory enables the pragma everywhere and tests inject invalid references to prove rejection.

**Integration and testing.** When two members' files overlap, merging against an explicit interface contract beat "replacing the files". Every test runs on a byte-copied database with the repository connection factory redirected to the copy, and every teardown re-hashes the baseline — making "we were careful" a checkable property.

# 8. References

1. Python Software Foundation. (n.d.). *sqlite3 — DB-API 2.0 interface for SQLite databases*. https://docs.python.org/3/library/sqlite3.html
2. Python Software Foundation. (n.d.). *threading — Thread-based parallelism*. https://docs.python.org/3/library/threading.html
3. Python Software Foundation. (n.d.). *unittest — Unit testing framework*. https://docs.python.org/3/library/unittest.html
4. Streamlit Inc. (n.d.). *Streamlit documentation*. https://docs.streamlit.io/
5. Streamlit Inc. (n.d.). *Session state*. https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
6. SQLite Consortium. (n.d.). *PRAGMA statements*. https://www.sqlite.org/pragma.html
7. SQLite Consortium. (n.d.). *Transactions*. https://www.sqlite.org/lang_transaction.html
8. SQLite Consortium. (n.d.). *File locking and concurrency in SQLite version 3*. https://www.sqlite.org/lockingv3.html

# 9. Links to Deliverables

- **Source code repository:** https://github.com/logic66-luoji/CampusMarket (public; directly accessible). Includes the database schema, backend logic, Streamlit front end, the SQLite baseline, and all test/generation scripts.
- **Video demonstration:** `presentation/video/CampusMarket-demo.mp4` (silent screencast with English captions burned in, 7 min 00 s; subtitle file: `CampusMarket-demo.srt`) — online copy (Google Drive, "anyone with the link"): https://drive.google.com/file/d/1FuaHKYJAehGgk3ynKA5npbew4nqjCl4I/view?usp=sharing
- **Supplementary materials in the repository:** `docs/` (audit, transaction-test, and integration reports), `tests/transactions/` + `tests/functional/` (test suites with run evidence), `presentation/` (video script, demo checklist, screenshots), `report/` (this report and figures).
