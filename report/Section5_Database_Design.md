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
