# 6. Evaluation and Results

All measurements were executed on 2026-11-21 against the delivered database (Windows 10, Python 3.10.0, SQLite 3.35.5; products = 10,000: 3,961 available / 6,039 sold), opened read-only; a 110,000-row scaled copy was used for the trend experiment and deleted afterwards.

**Query efficiency.** `EXPLAIN QUERY PLAN` confirms the marketplace query is executed as `SEARCH … USING INDEX idx_products_category_status`, while disabling the index (`category_id + 0 = 1`) falls back to `SCAN TABLE`. Averaged over 500 warm executions, the index reduces pure traversal cost (`SELECT COUNT(*)`, fully covered by the index) by **8.2×** at 10,000 rows and **12.8×** at 110,000 rows:

| Table size | Indexed (covering seek) | Forced scan | Ratio |
| ---: | ---: | ---: | ---: |
| 10,000 rows | 0.038 ms | 0.313 ms | 8.2× |
| 110,000 rows | 0.235 ms | 3.021 ms | 12.8× |

For the full row-returning query, end-to-end latency is dominated by materialising the 791 matching rows (1.52 ms indexed vs 1.72 ms scanned at 10k rows, 1.1×) — the index keeps traversal cost proportional to the result set rather than the table, an advantage that grows with data volume.

**Integrity, concurrency, and usability.** Thirteen automated tests (`tests/`) all pass: the ten consistency rules (foreign-key validity, sold/available invariants, price/status domains) hold on all 10,000 baseline rows with zero violations, and CHECK/foreign-key violations are provably rejected with `IntegrityError`; in ten barrier-synchronized two-thread purchase races on the real `buy_product()`, every round ended with exactly one winner and one loser, the row always `sold` with the winner's `buyer_id` and a non-NULL `finished_at`; and the four Streamlit pages plus the complete purchase workflow were verified live in a browser (screenshots in `presentation/screenshots/`).
