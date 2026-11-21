# Final Report — Consistency Check Log (Member C, 2026-11-21)

> **2026-11-21 restructure (v2):** the report was rewritten to the course's
> official submission outline (Group Information / Contribution Statement /
> Project Overview / Technical Design / Database Design / Evaluation and
> Results / Challenges and Lessons Learned / References / Links to
> Deliverables) in a condensed form. Member attributions now appear only in
> the Contribution Statement. New items required by the official template
> were added: **ER diagram** (Figure 2, drawn as SVG + PNG), **normalization
> level** (3NF, §5.3), and **sample queries** (§5.6). The buyer-workflow
> figure was renumbered to Figure 3. Undergraduate majors were restored and
> filled (A: Financial Mathematics; B: Economics; C: Communication
> Engineering). The PDF is delivered under the official-style name
> `CampusMarket-report.pdf`; `Final_Report.md` remains the editable source,
> and all nine `Section*.md` files mirror it. Sections 3/4 are condensed
> versions of B's original draft (full text preserved in git history and in
> the original `section3&4.md`).

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
   → `report/figures/Figure1/2…png`. The figures themselves were later drawn
   by Member C (2026-11-21) as SVG + PNG exports matching B's stated figure
   titles and content scope.
2. **§4.6 project tree**: extended with `tests/` and C's `docs/C_*.md`
   entries so the reported structure equals the delivered structure. No
   wording of B's prose was changed.
3. Everything else in Sections 3 and 4 is integrated verbatim from
   `section3&4.md`.

## 3. Pending inputs (tracked, not invented)

| Pending item | Owner | Placeholder location |
| --- | --- | --- |
| ~~Member names~~ → **DONE 2026-11-21**: A. Wang Fangcheng 72640065; B. Cai Haoneng 72640692; C. Li Jijia 72640201 | ~~Group~~ | §1.1 filled |
| ~~Undergraduate majors~~ → **REMOVED by group decision (2026-11-21)**: Section 1 lists name + student ID only | ~~Group~~ | §1.1 |
| ~~Section 5 Database Design~~ → **DONE 2026-11-21**: drafted by C from A's delivered `schema.sql` / DB audit, group-approved arrangement | ~~A~~ | §5 filled, drafting note included |
| ~~Section 6 Evaluation and Results~~ → **DONE 2026-11-21**: drafted by C from A's `performance_test.py` + real benchmark runs (see below) | ~~A~~ | §6 filled, drafting note included |
| ~~Figures 1 & 2~~ → **DONE 2026-11-21**: drawn by C (SVG source + PNG export in `report/figures/`) | ~~B~~ | `report/figures/` |
| GitHub repository URL → **DONE 2026-11-21**: https://github.com/logic66-luoji/CampusMarket (private) | ~~Group~~ | §9.1 filled |
| Demonstration video URL | Group | §9.2 (only remaining placeholder) |
| ~~Final PDF export~~ → done after Sections 5/6 landed (see `report/Final_Report.pdf`) | C | — |

### §6 measurement provenance (for the drafting note above)

All §6 numbers come from real runs on 2026-11-21 against the delivered
database opened read-only: `EXPLAIN QUERY PLAN` for both plans; 500-iteration
`SELECT *` benchmark (1.52 vs 1.72 ms at 10k rows; 24.80 vs 28.67 ms at
110k rows); covering-index `COUNT(*)` benchmark (0.038 vs 0.313 ms at 10k
rows = 8.2×; 0.235 vs 3.021 ms at 110k rows = 12.8×). The 110k-row
experiment used a temporary copy of the database (10 additional copies of
the products table), deleted afterwards; the baseline file was hash-verified
untouched.

## 4. Terminology decisions (uniform across all sections)

- English term for 成交状态：`status` ∈ `available` / `sold`; "transaction
  completion time" for `finished_at`; "purchase history" for the
  `get_my_purchases` page (NOT "orders").
- Data access layer functions are cited with their exact Python names
  (`buy_product`, `get_my_purchases`, `get_product_detail`,
  `get_user_products`).
- Table/column names always in code font, matching `schema.sql`.
