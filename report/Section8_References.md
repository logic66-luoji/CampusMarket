# 8. References

All references below are official documentation that the team actually
consulted during development (schema and pragma usage, Python database API
and testing modules, Streamlit state management, SQLite locking behavior for
the concurrency design). Each URL was verified accessible on 2026-11-21.

1. Python Software Foundation. (n.d.). *sqlite3 — DB-API 2.0 interface for
   SQLite databases*. Python 3 documentation.
   https://docs.python.org/3/library/sqlite3.html

2. Python Software Foundation. (n.d.). *threading — Thread-based
   parallelism*. Python 3 documentation.
   https://docs.python.org/3/library/threading.html

3. Python Software Foundation. (n.d.). *unittest — Unit testing framework*.
   Python 3 documentation. https://docs.python.org/3/library/unittest.html

4. Streamlit Inc. (n.d.). *Streamlit documentation*.
   https://docs.streamlit.io/

5. Streamlit Inc. (n.d.). *Session state — Streamlit docs*.
   https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state

6. SQLite Consortium. (n.d.). *PRAGMA statements*.
   https://www.sqlite.org/pragma.html

7. SQLite Consortium. (n.d.). *Transactions* (BEGIN/COMMIT/ROLLBACK).
   https://www.sqlite.org/lang_transaction.html

8. SQLite Consortium. (n.d.). *File locking and concurrency in SQLite
   version 3*. https://www.sqlite.org/lockingv3.html

## In-text citation mapping

| Report location | Reference(s) |
| --- | --- |
| Connection factory: `PRAGMA foreign_keys`, `sqlite3.Row` (§4.2, §7.3, §7.4) | 1, 6 |
| Purchase transaction and conditional UPDATE (§4.4, §7.2) | 1, 7 |
| Concurrency design and lock serialization; concurrency test (§4.4, §7.2, §7.6) | 2, 8 |
| Test suite construction (§7.6) | 3 |
| Test-account session context and page navigation (§3.4, §4.4) | 4, 5 |
