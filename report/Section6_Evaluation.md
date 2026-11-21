# 6. Evaluation and Results

> Drafting note: assembled by Member C from Member A's delivered
> `performance_test.py` and from benchmark runs executed on 2026-11-21
> against the delivered `campus_market.db` (opened read-only). All numbers
> below are from real runs; the scaled experiment operated on a temporary
> database copy which was deleted afterwards, leaving the baseline untouched.

## 6.1 Evaluation Setup

| Item | Value |
| --- | --- |
| OS | Windows 10 (10.0.22621, 64-bit) |
| Python / SQLite | 3.10.0 / 3.35.5 (stdlib `sqlite3`) |
| Database | delivered `campus_market.db` (users 1,000 / categories 5 / products 10,000) |
| Queries under test | `SELECT * FROM products WHERE category_id = 1 AND status = 'available'` — the marketplace filter in Section 4.4 |
| Methods | (a) `EXPLAIN QUERY PLAN` structural analysis; (b) repeated-execution timing on a read-only connection; (c) a scaled experiment on a temporary 110,000-row copy to expose the trend that a 10,000-row baseline cannot show |

The indexed variant runs the query as written; the comparison variant forces
a full scan by wrapping the filter column in an arithmetic expression
(`category_id + 0 = 1`), which prevents index selection — the same technique
used in A's `performance_test.py`.

## 6.2 Query Plan Analysis

`EXPLAIN QUERY PLAN` confirms that SQLite selects the composite index for
the marketplace query, and that disabling index selection falls back to a
scan:

```text
-- as written (index usable)
SEARCH TABLE products USING INDEX idx_products_category_status
    (category_id=? AND status=?)

-- category_id + 0 = 1 (index disabled on purpose)
SCAN TABLE products
```

`SEARCH` visits only the matching index range (category 1, status
'available') and follows row references; `SCAN` reads all 10,000 rows and
filters. This structural difference holds at every dataset size and is the
primary correctness evidence that the index is wired into the query path.

## 6.3 Index Performance Results

### 6.3.1 Whole-row query (`SELECT *`) — the application's real query

A's original single-shot timing (`performance_test.py`) reports millisecond
level times on both paths; five consecutive runs produced overlapping
ranges (indexed 0.00–5.85 ms; full scan 2.79–11.87 ms) because the OS page
cache warms the file after the first read. To obtain stable figures we
averaged **500 executions** on one warm read-only connection:

| Table size | Indexed | Forced full scan | Ratio |
| ---: | ---: | ---: | ---: |
| 10,000 rows | 1.52 ms/query | 1.72 ms/query | 1.1× |
| 110,000 rows | 24.80 ms/query | 28.67 ms/query | 1.2× |

The modest gap is an honest and instructive result: this query *returns*
791 rows at the baseline size (8,700 at the scaled size), and materialising
those rows dominates the total cost at every scale. The index saves only the
traversal portion, so when traversal is a small share of total cost, the
end-to-end gain stays small.

### 6.3.2 Pure traversal (`SELECT COUNT(*)`) — isolating the index effect

To measure the traversal cost alone we timed a `COUNT(*)` aggregate, which
needs no row materialisation and is fully satisfied by the covering index
(`COUNT` appears in neither benchmark's returned rows):

| Table size | Indexed (covering-index seek) | Forced scan | Ratio |
| ---: | ---: | ---: | ---: |
| 10,000 rows | 0.038 ms | 0.313 ms | **8.2×** |
| 110,000 rows | 0.235 ms | 3.021 ms | **12.8×** |

Two findings follow. First, the composite index does its job: the indexed
plan is a `SEARCH ... USING COVERING INDEX` seek over the matching range,
versus a linear scan. Second, the advantage **grows with dataset size** —
the seek cost scales with the matching entries while the scan cost scales
with the whole table, so the ratio rose from 8.2× at 10,000 rows to 12.8×
at 110,000 rows and continues to diverge as data grows.

### 6.3.3 Interpretation

The experiments support the indexing decision of Section 5.6 while being
precise about its scope: at the current 10,000-row baseline everything fits
in memory and absolute latencies are milliseconds regardless of plan; the
composite index becomes structurally important as the listing table grows
or when the buffer is cold, and it keeps the marketplace query's traversal
cost proportional to the result set rather than to the table. The
application-side benefit is visible today in the query plan (`SEARCH` not
`SCAN`) and in the traversal benchmark; whole-row end-to-end gains remain
modest because row materialisation, not data access, dominates at this
scale.

## 6.4 Transaction, Integrity, and Functional Verification

The database-side guarantees were additionally verified by Member C's
automated suites (`docs/C_Transaction_Test_Report.md`; 13/13 tests passing
on 2026-11-21):

- **Integrity**: all ten consistency rules (foreign-key validity, the
  sold/available invariants of Section 5.4, price and status domains) hold
  on the full 10,000-row baseline with 0 violations, and `PRAGMA
  foreign_key_check` reports none; CHECK and foreign-key constraints
  provably reject invalid writes with `IntegrityError`.
- **Concurrency**: ten barrier-synchronized two-thread races on the real
  `buy_product()` conditional UPDATE produced exactly one winner and one
  loser per round, with the final row always `sold`, bearing the winner's
  `buyer_id` and a non-NULL `finished_at`.
- **Functional walkthrough**: the publish → browse → purchase → history →
  management journey passes end-to-end at the service layer, and the
  Streamlit application was additionally verified live in a browser
  (`docs/C_Integration_Report.md` §5.1).

## 6.5 Summary

The delivered three-table schema satisfies the application's information
needs with two purpose-built indexes. Query-plan analysis proves the
composite index is selected for marketplace filtering; repeated-execution
benchmarks quantify an 8.2×–12.8× traversal advantage that widens with data
volume, while honestly recording that whole-row query latency at the 10k
baseline is dominated by row materialisation. Integrity, concurrency, and
functional suites complement the performance evaluation and confirm the
behaviour claimed in Sections 3 and 4.
