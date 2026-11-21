# 2. Contribution Statement

All three members contributed to a shared Git working tree and coordinated
handovers through written handover documents (`docs/` in the project
repository). The statements below describe the work each member actually
completed and delivered.

## 2.1 Member A — Database Design and Construction (Wang Fangcheng, 72640065)

- Designed the relational schema for the platform and maintained the DDL file
  (`database/schema.sql`), covering the `users`, `categories`, and `products`
  tables with primary keys, foreign keys, and CHECK constraints.
- Constructed the SQLite database (`database/campus_market.db`) and prepared
  the synthetic dataset of 1,000 users, 5 categories, and 10,000 products
  (3,961 available / 6,039 sold in the delivered baseline snapshot),
  including campus-oriented Chinese product descriptions.
- Implemented the purchase-related data access interfaces
  (`buy_product`, `get_my_purchases`) in the update package that introduced
  the buyer/transaction fields into the `products` table.
- Implemented and maintained the index performance experiment script
  (`performance_test.py`) and the early repository self-test script
  (`test_repo.py`).
- Responsible for the database-related report sections (Section 5, Database
  Design; Section 6, Evaluation and Results).

## 2.2 Member B — Application Architecture and Development (Cai Haoneng, 72640692)

- Established the unified database connection factory
  (`database/connection.py`) with an absolute database path, per-connection
  foreign-key enforcement, and `sqlite3.Row` result rows.
- Developed the data access layer: product filtering with a sorting
  whitelist, `LIMIT`/`OFFSET` pagination, product publishing, editing, and
  deletion in `product_repository.py`; read-only `user_repository.py` and
  `category_repository.py`.
- Merged A's 2026-11-19 update package into the application: preserved the
  existing repository functions, adapted `buy_product` into a single
  transaction with a conditional UPDATE, and replaced the database file with
  the regenerated baseline.
- Developed the business logic layer (`product_service.py`,
  `user_service.py`) with input validation and the test-account session
  context, and built the Streamlit presentation layer: the entry page, the
  marketplace page, the product detail/purchase page, the seller management
  page, and the purchase history page.
- Provided the integration self-check script (`check_interfaces.py`) and the
  developer handover documentation.
- Responsible for the application-related report sections (Section 3,
  Project Overview; Section 4, Technical Design).

## 2.3 Member C — Integration, Testing, and Reporting (Li Jijia, 72640201)

- Audited the delivered codebase and database (read-only verification of the
  schema, constraints, indexes, data snapshot, and layer boundaries) and
  produced the audit report (`docs/C_Project_Audit.md`).
- Designed and implemented the transaction and concurrency test suite
  (`tests/transactions/`) on isolated database copies: normal purchase,
  duplicate purchase, self-purchase, nonexistent product, multi-threaded
  concurrent purchase with `threading.Barrier` (10 rounds, exactly one
  winner per round), and data integrity/constraint enforcement tests.
- Implemented the service-layer end-to-end functional walkthrough
  (`tests/functional/test_workflow_integration.py`) covering the complete
  user journey across the four application pages, and produced the test and
  integration reports (`docs/C_Transaction_Test_Report.md`,
  `docs/C_Integration_Report.md`).
- Documented challenges and lessons learned; compiled and verified the
  reference list; organized deliverable links.
- Integrated the final report (Sections 1, 2, 7, 8, 9 and the consistency
  check across all sections) and prepared the demonstration video script and
  checklist.
