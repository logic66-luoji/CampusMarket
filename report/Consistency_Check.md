# Final Report — Consistency Check Log (Member C, 2026-11-21)

Task 5 requires the consolidated report to be internally consistent with the
delivered code. This log records every check performed and every editorial
change made during consolidation, so teammates can review and object before
submission.

## 1. Checks against the actual codebase

| # | Check | Method | Result |
| --- | --- | --- | --- |
| 1 | No obsolete `orders`-table description anywhere in the report | text search over Final_Report.md | ✅ All `orders` mentions are explicit "removed" statements (§4.4, §7.1, §5 note) |
| 2 | Purchase logic described as conditional UPDATE on `products` | comparison with `product_repository.buy_product` | ✅ §4.4 SQL block matches the delivered implementation (incl. `rowcount` decision) |
| 3 | Test accounts NOT described as a full authentication system | comparison with `user_service.py` scope decision | ✅ §3.4/§3.5 describe "predefined test accounts … not a fully implemented registration and authentication mechanism" |
| 4 | Only `available`/`sold` states described (no invented state machine) | comparison with schema CHECK + pages | ✅ |
| 5 | All named pages/functions exist in code | AST cross-check (see docs/C_Integration_Report.md §4) | ✅ |
| 6 | Data scale consistent across sections | grep + DB read-only verification | ✅ 1,000 / 5 / 10,000 used everywhere; available/sold = **3,961/6,039** (actual), matching docs/C_Project_Audit.md §6.1. The earlier 3,964/6,036 figure appears only in the §5 editorial note as an explicit correction request to A |
| 7 | Performance figures real | `performance_test.py` run on 2026-11-21 | ✅ §6 note cites the real measured values (~0 ms vs ~11.9 ms) |
| 8 | Test results real | unittest run records | ✅ 13 tests pass; 10 concurrency rounds in `tests/transactions/results/concurrency_runs.json` |
| 9 | References genuine and accessible | WebFetch verification on 2026-11-21 | ✅ 8/8 URLs confirmed; no DOIs/authors/titles fabricated |
| 10 | No invented features | feature list vs code | ✅ Payment/reviews/image upload/auth explicitly out of scope; `image_url` described as reserved field |

## 2. Editorial changes made to B's Sections 3–4 (only these)

1. **Figure paths**: `C:\Users\25431\...\Figure1/2….png` (author-local paths)
   → `report/figures/Figure1/2…png` with a placeholder note. Figures
   themselves are pending export by B.
2. **§4.6 project tree**: extended with `tests/` and C's `docs/C_*.md`
   entries so the reported structure equals the delivered structure. No
   wording of B's prose was changed.
3. Everything else in Sections 3 and 4 is integrated verbatim from
   `section3&4.md`.

## 3. Pending inputs (tracked, not invented)

| Pending item | Owner | Placeholder location |
| --- | --- | --- |
| ~~Member names~~ → **DONE 2026-11-21**: A. Wang Fangcheng 72640065; B. Cai Haoneng 72640692; C. Li Jijia 72640201 | ~~Group~~ | §1.1 filled |
| Undergraduate majors | Group | §1.1 (only remaining §1 placeholder) |
| Section 5 Database Design | A | §5 "[TO BE PROVIDED BY MEMBER A]" with agreed outline |
| Section 6 Evaluation and Results | A | §6 "[TO BE PROVIDED BY MEMBER A]" with agreed outline |
| Figures 1 & 2 export | B | `report/figures/` |
| GitHub repository URL | Group | §9.1 |
| Demonstration video URL | Group | §9.2 |
| Final PDF/DOCX export | C (mechanical) | after A's sections arrive |

## 4. Terminology decisions (uniform across all sections)

- English term for 成交状态：`status` ∈ `available` / `sold`; "transaction
  completion time" for `finished_at`; "purchase history" for the
  `get_my_purchases` page (NOT "orders").
- Data access layer functions are cited with their exact Python names
  (`buy_product`, `get_my_purchases`, `get_product_detail`,
  `get_user_products`).
- Table/column names always in code font, matching `schema.sql`.
