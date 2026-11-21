# 4. Technical Design

| Technology | Role |
| --- | --- |
| Python 3 (stdlib `sqlite3`, `unittest`, `threading`) | Application language, database driver, test framework |
| Streamlit ≥ 1.31 | Web front end: entry page + four business pages, session state |
| SQLite (`campus_market.db`) | Embedded relational database, no server deployment |
| pandas / Faker | Supporting dependencies for the data-preparation workflow (archived `seed.py`) |

The application follows a three-layer architecture. The **presentation layer** (Streamlit pages) renders UI and holds the current test account in session state, but contains no SQL and no database connections. The **business logic layer** (`product_service.py`, `user_service.py`) validates input, assembles search parameters, and orchestrates operations. The **data access layer** (`repositories/`) is the only place where SQL is written: all statements are parameterized, sort expressions come from a fixed whitelist, and ownership checks are embedded in UPDATE/DELETE `WHERE` clauses. Every connection is obtained from a single factory (`database/connection.py`) that uses an absolute file path, enables `PRAGMA foreign_keys = ON` per connection, and returns `sqlite3.Row` rows. Figure 1 shows the layers and their dependencies.

![](report/figures/Figure1_CampusMarket_Architecture.png)
