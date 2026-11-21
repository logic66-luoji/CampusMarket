# CampusMarket Demonstration Video Script (English, target 5:30–7:00)

Recording basis: the running CampusMarket Streamlit application
(`streamlit run app.py`) and the delivered repository. **Status: script and
checklist prepared; the video itself is to be recorded in an environment
with Streamlit installed** (see Demo_Checklist.md for the preconditions).
Do not present any feature that is not reproducible in the final build.

On-screen conventions: speak at a moderate pace; whenever a Chinese UI
element is shown, say its English meaning; keep the sidebar account switcher
visible whenever identity matters.

Demo data to prepare before recording (see Demo_Checklist.md §3):
- Seller account: the sidebar account that will publish the demo product
  (recommended: the account used in rehearsal, e.g. `#1 user_0_ndai`).
- Buyer account: a different sidebar account (e.g. the next one in the list).
- One dedicated demo product titled `DEMO Used Textbook - Calculus 7th Ed`,
  price 45.00, category 书籍教材 (Textbooks), published fresh in the seller
  session right before Part 4/5 (published through the app itself — never by
  editing the database).

---

## Part 1 — Introduction (0:00–0:40, ~40 s)

**[Screen: app.py home page]**

> "Hello, this is CampusMarket, our campus second-hand trading platform,
> built for the Database Systems course, Track 1. It lets students publish,
> browse, and purchase used items — textbooks, electronics, daily goods.
> Our goal was not just a working interface, but a platform that
> demonstrates relational database design in a real application: integrity
> constraints, indexing, and transactional purchases. The stack is Python
> with Streamlit for the web front end, and SQLite as the embedded
> relational database. One note before we start: login is simulated with
> predefined test accounts in the sidebar — the project scope focuses on the
> database layer, so there is no registration or password flow."

## Part 2 — System Architecture (0:40–1:40, ~60 s)

**[Screen: Figure 1 architecture diagram, then the project tree]**

> "The system follows a three-layer architecture. The presentation layer is
> Streamlit — an entry page plus four business pages. The business logic
> layer is two Python service modules that validate input and orchestrate
> operations. The data access layer is repository modules where **all** SQL
> lives. Pages never write SQL; services never write SQL; every connection
> comes from one connection factory that enables foreign keys with
> `PRAGMA foreign_keys = ON` and returns rows as dictionaries. Underneath,
> SQLite stores three tables: users, categories, and products. Purchases are
> recorded directly on the product row — there is no separate orders table;
> buyer ID, status, and completion time live in the products table itself."

## Part 3 — Product Browsing (1:40–2:40, ~60 s)

**[Screen: pages/1_Marketplace.py]**

> "The marketplace page queries only products whose status is available.
> All filtering happens in parameterized SQL. Let me search by keyword —
> I'll type the Chinese word for mouse, because the dataset uses Chinese
> titles. Next, filter by category — Electronics. And by price range — say
> 10 to 100 yuan. I can sort by price, highest first, or by publish time.
> Results are paginated: twenty per page, with a count query computing the
> total, so I can page through eight thousand-plus available items
> efficiently. The composite index on category and status makes these
> filtered lookups fast — we'll see the numbers in Part 6."

## Part 4 — Seller Operations (2:40–3:40, ~60 s)

**[Screen: pages/3_Sell_MyProducts.py, seller account selected]**

> "I'm now a seller. Publishing is validated at the service layer — title
> length, category, and a positive price — then inserted by the repository.
> Let me publish our demo product: 'DEMO Used Textbook - Calculus 7th
> Edition', category Textbooks, price 45 yuan. It appears in 'My Products'
> with status available. Editing works the same way — I'll change the price
> to 39.5 — and the update statement includes my seller ID in its WHERE
> clause, so I can only edit my own listings. Sold products stay in the list
> with their transaction record, and the delete button is deliberately
> hidden for them, so a completed sale can never be erased."

## Part 5 — Purchase Workflow (3:40–5:10, ~90 s) ★ core part

**[Screen: switch account → marketplace → detail → buy → redirect]**

> "Now the core transaction. I switch the sidebar account to a buyer — this
> is how identity is represented in session state. In the marketplace I
> search for the demo product and open its detail page. The detail shows
> seller, category, price, and the buy section, which explains that the
> purchase is one transaction: a conditional UPDATE that sets buyer ID,
> status 'sold', and finished-at, only while the row is still available.
> Clicking Purchase — success. The app redirects me to My Purchases: one
> record, 39.5 yuan, category filtering above the list, and the exact
> completion time stored in the database. Let me go back to the same
> product and try to buy it again: 'This product has already been taken by
> someone else' — rejected, because the UPDATE affected zero rows. Back in
> the seller account, the product now shows 'sold' with the buyer ID and
> completion time. One product, exactly one buyer — guaranteed by the
> database, not by the interface."

## Part 6 — Database and Testing (5:10–6:30, ~80 s)

**[Screen: DB browser or SQL REPL + test run]**

> "Under the hood: three tables, with foreign keys from products to users
> — both seller and buyer — and to categories, plus CHECK constraints on
> price and status. Two indexes support the two hot queries: category plus
> status for browsing, buyer ID for purchase history. This is the explain
> plan of the marketplace query — it searches the composite index rather
> than scanning ten thousand rows; the index comparison script measures the
> difference. For correctness, we run thirteen automated tests on isolated
> copies of the database: normal, duplicate, self, and nonexistent-product
> purchases; data integrity rules; and — most importantly — real concurrent
> purchases: two threads hit 'Buy' at the same instant through a barrier,
> and in all ten rounds exactly one thread won, the other got the failure
> message, and the row ended up sold with exactly one buyer. The baseline
> database is hash-checked by every test teardown, so testing can never
> corrupt the delivered data."

## Part 7 — Conclusion (6:30–7:00, ~30 s)

**[Screen: home page]**

> "To conclude: CampusMarket is a complete campus trading workflow —
> publish, browse, buy, and review — on a three-table relational schema.
> Its transactional, conditional update guarantees exactly-once purchases;
> foreign keys, CHECK constraints, and indexes demonstrate applied database
> design; and thirteen automated tests, including genuine concurrency races,
> verify the behavior. Thank you for watching — the repository link and the
> full report are below."

---

## Timing summary

| Part | Budget | Content |
| --- | --- | --- |
| 1 Introduction | 0:40 | project, users, stack, account-simulation disclaimer |
| 2 Architecture | 1:00 | three layers, connection factory, no-orders model |
| 3 Browsing | 1:00 | keyword / category / price / sort / pagination |
| 4 Seller ops | 1:00 | publish → edit → ownership rule → sold rows kept |
| 5 Purchase workflow ★ | 1:30 | buy → redirect → history → duplicate rejection → seller view |
| 6 Database & testing | 1:20 | schema, FK/CHECK, indexes, EXPLAIN, 13 tests, concurrency rounds |
| 7 Conclusion | 0:30 | summary |
| **Total** | **~7:00** | within the 5–8 minute requirement |

## Narration cautions

1. Do **not** describe the test-account switcher as login/authentication.
2. Do **not** mention any "order table" or "order states" — only available/sold.
3. Do **not** show real passwords or password hashes on screen (the users
   table stores hashes; do not open that column in the DB view).
4. Keyword demos must use Chinese keywords (dataset is Chinese); translate
   each on-screen term verbally.
5. Every claim in Parts 3–6 maps to a verified behavior listed in
   Demo_Checklist.md — if a step fails on recording day, fix the step, not
   the narration.
