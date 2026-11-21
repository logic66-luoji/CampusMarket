# 5. Database Design

> Drafting note: this section was assembled by Member C from Member A's
> delivered database artifacts — the shipped `database/schema.sql`, the
> delivered `campus_market.db`, and the read-only audit performed on
> 2026-11-21. Every table, column, constraint, and count stated below was
> verified against the delivered database file (see `docs/C_Project_Audit.md`).

## 5.1 Design Overview

The database stores three entities: **users**, **categories**, and
**products**. An earlier iteration of the design used a fourth `orders`
table for purchase records; during the 2026-11-19 dataset regeneration the
team removed it and moved transaction state onto the product row itself
(`buyer_id`, `status`, `finished_at`). The delivered model is therefore:

```text
users 1 ──────── * products * ──────── 1 categories
           (seller_id)   │  (buyer_id, nullable)
                         └──── 1 users (as buyer)
```

- One user (seller) publishes many products: `products.seller_id → users.user_id`.
- One category contains many products: `products.category_id → categories.category_id`.
- A purchase does **not** create a new row; it updates the product row with
  the buyer, the `sold` status, and a completion timestamp. One user (buyer)
  has many purchased products through `products.buyer_id → users.user_id`,
  which is `NULL` while the product is unsold.

## 5.2 Relational Schema

The delivered `database/schema.sql` matches the DDL stored in the delivered
`campus_market.db` byte-for-byte. The three table definitions are:

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
    FOREIGN KEY (seller_id)   REFERENCES users(user_id)      ON DELETE CASCADE,
    FOREIGN KEY (buyer_id)    REFERENCES users(user_id)      ON DELETE SET NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT
);
```

## 5.3 Field-Level Description

**`products`** (the central table):

| Column | Type | Constraint | Meaning |
| --- | --- | --- | --- |
| `product_id` | INTEGER | PK, AUTOINCREMENT | Surrogate identifier of the listing |
| `seller_id` | INTEGER | NOT NULL, FK → users, CASCADE | Publisher of the product |
| `buyer_id` | INTEGER | NULLable, FK → users, SET NULL | Purchaser; **NULL while unsold**, set by `buy_product()` |
| `category_id` | INTEGER | NOT NULL, FK → categories, RESTRICT | Category membership |
| `title` | VARCHAR(100) | NOT NULL | Display title (campus-oriented Chinese text) |
| `description` | TEXT | optional | Free-text description |
| `price` | DECIMAL(10,2) | NOT NULL, CHECK ≥ 0 | Listed price in CNY |
| `status` | VARCHAR(20) | DEFAULT 'available', CHECK ∈ {available, sold} | Transaction state stored on the product row |
| `image_url` | VARCHAR(255) | reserved | Not used by the current UI scope |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Publication time |
| `finished_at` | TIMESTAMP | NULLable | Transaction completion time; **NULL while unsold** |

**`users`**: surrogate `user_id`; `username` and `email` are UNIQUE;
`password_hash` stores a SHA-256 hash written during dataset preparation
(the current application scope uses predefined test accounts and does not
implement authentication). **`categories`**: surrogate `category_id` and a
UNIQUE `name`.

## 5.4 Referential Integrity

The three foreign-key actions were chosen per relationship:

- **seller_id → CASCADE**: deleting a user removes that user's listings, so
  no orphaned seller rows can remain.
- **buyer_id → SET NULL**: deleting a user preserves the product (and the
  historical sale row) while clearing the purchaser reference.
- **category_id → RESTRICT**: a category with products cannot be deleted,
  keeping the marketplace's five categories intact.

A design nuance worth recording: `SET NULL` on `buyer_id` can, in theory,
leave a `sold` row without a buyer if a user account were deleted — but the
application exposes no user-deletion operation, so the invariant
*“sold → buyer_id IS NOT NULL AND finished_at IS NOT NULL;
available → both are NULL”* holds. Member C's integrity suite
(`tests/transactions/test_integrity.py`) verified all ten consistency rules
against the full 10,000-row baseline (0 violations) and confirmed that
invalid references are rejected at insert/update time
(`PRAGMA foreign_keys = ON` is enforced by the connection factory on every
connection, since SQLite stores this pragma per-connection rather than in
the file).

## 5.5 CHECK Constraints and Defaults

- `price >= 0` rejects negative prices at the database level.
- `status IN ('available', 'sold')` admits exactly the two workflow states —
  the delivered model deliberately has no richer order-state machine.
- Defaults: `status = 'available'`, `created_at = CURRENT_TIMESTAMP`,
  `buyer_id`/`finished_at` NULL — a newly published product is on sale with
  an empty transaction record.

## 5.6 Indexes

Two indexes ship with the delivered database, each supporting one hot query
path of the application:

| Index | Columns | Supporting query |
| --- | --- | --- |
| `idx_products_category_status` | (`category_id`, `status`) | Marketplace browsing: `WHERE status = 'available' [AND category_id = ?]` — the composite column order matches the filter, enabling index seeks (Section 6) |
| `idx_products_buyer` | (`buyer_id`) | Purchase history: `WHERE buyer_id = ? AND status = 'sold'` in `get_my_purchases()` |

## 5.7 Dataset Description

The delivered baseline `campus_market.db` contains:

| Table | Rows | Notes |
| --- | ---: | --- |
| users | 1,000 | user_id 1–1000, synthetic usernames/emails, SHA-256 password hashes |
| categories | 5 | 电子产品, 书籍教材, 生活用品, 服饰鞋包, 运动户外 (Electronics, Textbooks, Daily Necessities, Clothing & Bags, Sports & Outdoor) |
| products | 10,000 | campus-oriented synthetic Chinese titles/descriptions (e.g., 「高数教材第七版」, 「毕业清仓 游戏鼠标」) |

Transaction-state distribution verified read-only on **2026-11-21**:
**3,961 available / 6,039 sold**. (Earlier handover documents cited
3,964/6,036; the audit traced the three-row difference to purchases made
during B's verification session on 2026-11-19 that were not restored. The
verified figures above are adopted throughout this report; see
`docs/C_Project_Audit.md` §6.1.) The 10,000-row product table is the fixed
baseline for the index experiments in Section 6 and is intentionally
shipped with the repository so the application runs without regeneration.
