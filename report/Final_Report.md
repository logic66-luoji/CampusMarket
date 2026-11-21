# CampusMarket — A Campus Second-hand Trading Platform

**Database Systems · Track 1 — Database Application Development**

---

> **Integration status (2026-11-21, prepared by Member C)**
>
> This consolidated report contains all nine sections in the required order.
> - Sections 3 and 4 are integrated from Member B's draft (`section3&4.md`).
> - Sections 5 and 6 were drafted by Member C **from Member A's delivered
>   database artifacts and from benchmark runs executed on 2026-11-21**;
>   every schema detail and number is verified against the shipped database
>   and stated measurement records. This drafting arrangement was decided by
>   the group.
> - Member names and student IDs are complete; the group decided not to
>   include undergraduate majors in this report.
> - The only outstanding placeholder is the video URL in Section 9.2.

## Contents

1. Group Information
2. Contribution Statement
3. Project Overview
4. Technical Design
5. Database Design
6. Evaluation and Results
7. Challenges and Lessons Learned
8. References
9. Links to Deliverables

---

# 1. Group Information

## 1.1 Group Members

| Member | Name | Student ID |
| --- | --- | --- |
| Member A | Wang Fangcheng（王方成） | 72640065 |
| Member B | Cai Haoneng（蔡浩能） | 72640692 |
| Member C | Li Jijia（李积佳） | 72640201 |

## 1.2 Course Information

- Course: Database Systems
- Project: CampusMarket — A Campus Second-hand Trading Platform
- Track: Track 1 — Database Application Development

---

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
- Drafted Sections 5 and 6 of the final report from Member A's delivered
  database artifacts and measured results, and drew the two report figures.
- Integrated the final report (Sections 1, 2, 7, 8, 9 and the consistency
  check across all sections) and prepared the demonstration video script and
  checklist.

---

# 3. Project Overview

## 3.1 Project Background and Motivation

The rapid development of online marketplaces has made second-hand trading an increasingly accessible way for individuals to exchange unused goods. Within university campuses, students frequently possess items such as textbooks, electronic devices, stationery, and daily necessities that remain usable but are no longer needed. At the same time, other students may be interested in purchasing these items at relatively affordable prices. However, campus-based second-hand transactions are often conducted through informal communication channels, including social media groups and personal networks. Such arrangements can make product discovery, information organization, and transaction tracking relatively inefficient.

CampusMarket is developed as a campus-oriented second-hand trading platform that provides a centralized environment for managing product information and facilitating basic transactions between students. Rather than focusing exclusively on the user interface, the project emphasizes the application of relational database concepts to a practical information management scenario. The system integrates product publishing, multi-condition searching, product management, and purchase recording within a database-driven web application.

From a database systems perspective, the project provides a practical setting for demonstrating relational data modeling, SQL-based data retrieval, integrity constraints, indexing, and transaction management. By separating the application into presentation, business logic, and data access layers, CampusMarket also illustrates how database operations can be integrated into a structured software application.

## 3.2 Problem Statement

A campus second-hand marketplace involves several interconnected types of information, including user accounts, product descriptions, product categories, and transaction records. Without a centralized data management mechanism, maintaining consistency among these records and retrieving relevant product information can become difficult.

CampusMarket addresses three main problems.

First, product information needs to be organized in a structured and searchable manner. Users should be able to identify relevant products based on keywords, categories, and price ranges, rather than relying on manually browsing unstructured listings.

Second, product ownership and transaction information must be managed consistently. A seller should only be able to modify or remove products they have published, while completed transactions should retain the corresponding buyer and completion information. In particular, the system must prevent multiple users from successfully purchasing the same product.

Third, database operations should be implemented through a maintainable and secure application structure. Directly embedding SQL statements in interface components can introduce unnecessary coupling between presentation and data management. Therefore, the application requires a clearly defined separation between user interaction, business rules, and database access.

To address these issues, CampusMarket adopts a relational database-backed architecture and implements controlled data access, parameterized SQL queries, and atomic conditional updates for purchase operations.

## 3.3 Application Goals

The primary objective of CampusMarket is to develop a functional web-based application that supports the essential operations of a campus second-hand marketplace while demonstrating the practical application of database system principles.

The specific objectives are as follows:

- **Structured information management:** Organize users, product categories, and product information using a relational database, with appropriate primary keys, foreign keys, and integrity constraints.
- **Efficient product discovery:** Provide keyword searching, category filtering, price-range filtering, sorting, and pagination to support efficient retrieval of available products.
- **Product lifecycle management:** Allow users to publish, edit, and delete their own products while preserving completed transaction records.
- **Transaction consistency:** Implement purchase operations using database transactions and conditional updates to prevent duplicate purchases of the same product.
- **Maintainable software design:** Separate the presentation layer, business logic layer, and data access layer to improve modularity and reduce dependencies between application components.
- **Practical database demonstration:** Provide a working application through which database operations, query processing, indexing, and transaction-related mechanisms can be demonstrated and evaluated.

The project deliberately focuses on essential marketplace operations rather than implementing an extensive commercial e-commerce system. Payment processing, logistics management, recommendation algorithms, and user-generated reviews are outside the current implementation scope.

## 3.4 Target Users

The primary target users are university students who wish to buy or sell second-hand products within their campus community.

From the seller's perspective, students can publish products with relevant information, including titles, descriptions, categories, and prices. They can subsequently review their listings, modify product information, and remove products that have not yet been sold.

From the buyer's perspective, students can browse available products, apply different search and filtering conditions, inspect product details, and purchase items. The system also provides a dedicated purchase history page through which buyers can review completed transactions and retrieve the corresponding product information.

For development and demonstration purposes, the current application uses predefined test accounts rather than a fully implemented registration and authentication mechanism. Users can switch between available test accounts through the application sidebar. This allows the system to simulate different buyer and seller identities and demonstrate the corresponding data relationships.

## 3.5 Core Functionalities

CampusMarket implements four principal functional areas, supported by a user context management mechanism.

**1. User Context Management**

The application provides a predefined set of user accounts stored in the database. Users can switch their current identity through a sidebar selector, with the selected user maintained in Streamlit session state. This mechanism supports the demonstration of different user operations without implementing a complete registration and password authentication workflow.

**2. Product Browsing and Search**

The marketplace module displays products that are currently available for purchase. Users can search by product title, filter listings by category and minimum or maximum price, and sort the results by publication time or price. The results are presented through a paginated interface, with a default page size of 20 products.

The underlying database queries use parameterized SQL statements. Sorting options are restricted to a predefined whitelist, while pagination is implemented using `LIMIT` and `OFFSET`. These mechanisms support controlled query execution and reduce unnecessary data retrieval.

**3. Product Management and Detail Inspection**

Users can publish new products by providing a title, category, price, and optional description. They can also edit the information of their own listings and delete products that have not been sold.

The product detail module provides more comprehensive information, including the product identifier, category, seller identifier, publication time, description, price, and current transaction status. For completed transactions, the system additionally displays the buyer identifier and transaction completion time.

Ownership restrictions are enforced at the data access level by including the seller identifier in update and delete conditions. Furthermore, completed products cannot be deleted, ensuring that transaction-related information remains available.

**4. Product Purchase and Purchase History**

The purchase module allows a user to purchase an available product, subject to two business rules: users cannot purchase their own products, and products that have already been sold cannot be purchased again.

Upon a successful purchase, the system updates the product's `buyer_id`, `status`, and `finished_at` fields within a database transaction. A conditional update requiring the product status to remain `available` ensures that only one competing purchase operation can successfully modify the product record.

Following a successful purchase, the application redirects the user to the purchase history page. This page retrieves completed purchases associated with the current buyer and displays the number of purchased products, cumulative purchase amount, latest transaction date, and individual transaction records. Users can also filter their purchase history by product category and revisit the corresponding product details.

Together, these functionalities establish a complete basic trading workflow, from product publication and discovery to purchase completion and transaction record retrieval.

---

# 4. Technical Design

## 4.1 Technology Stack

CampusMarket adopts a Python-based technology stack consisting of Streamlit, SQLite, and SQL, supported by several libraries for data processing and development. The technology choices are intended to provide a lightweight development environment while maintaining sufficient functionality for demonstrating database application concepts.

| Technology   | Purpose and Application                                      |
| ------------ | ------------------------------------------------------------ |
| Python 3.13+ | Main programming language for application development, business logic, and database interaction. |
| Streamlit    | Web application framework used to construct interactive pages, navigation, forms, and user interface components. |
| SQLite       | Embedded relational database used to persist user, category, and product information without requiring a separate database server. |
| SQL          | Used for relational data manipulation, conditional queries, filtering, sorting, and transaction operations. |
| Pandas       | Supporting library for structured data processing and potential analysis of experimental datasets. |
| Faker        | Supporting library for synthetic test-data generation in the database preparation workflow. |
| Git / GitHub | Version control and collaborative development.               |

Python serves as the central implementation language, connecting the user interface with the underlying database. Streamlit provides the presentation framework and manages application interactions through its session-state mechanism. SQLite is selected as the database engine because it provides relational database capabilities with minimal deployment overhead, making it suitable for a lightweight campus marketplace application.

SQL operations are encapsulated within the repository layer rather than being embedded directly in Streamlit pages. This design establishes a consistent interface for database access and allows business rules to be implemented independently of the underlying SQL statements.

The core application dependencies are Streamlit and the Python standard library's SQLite interface. Pandas and Faker are included as supporting dependencies for data-related operations. The current implementation does not require a separately deployed database server.

## 4.2 Software Architecture

CampusMarket follows a three-layer software architecture consisting of the Presentation Layer, Business Logic Layer, and Data Access Layer, supported by an SQLite database.

This architecture separates user interaction from business operations and persistent data management. Each layer has a clearly defined responsibility and communicates with adjacent layers through function calls and structured return values.

**Presentation Layer**

The presentation layer is implemented using Streamlit and is responsible for displaying application pages and receiving user input. It includes the application entry point (`app.py`) and four functional pages covering product browsing, product details and purchasing, product publishing and management, and purchase history.

This layer handles interface rendering, form submission, navigation, and session-state management. It does not directly execute SQL statements or establish database connections. Instead, it invokes service-layer functions to perform the required operations.

**Business Logic Layer**

The business logic layer is implemented through Python service modules, primarily `user_service.py` and `product_service.py`.

The user service manages the current user context, retrieves available test accounts, and maintains the selected user identifier in Streamlit session state. The product service handles product-related business rules, including input validation, search parameter construction, product publication, product modification, deletion restrictions, and purchase operations.

For example, before publishing a product, the service layer validates its title, category, description, and price. Similarly, before deleting a product, it checks whether the product has already been sold. These validations prevent invalid operations from being passed directly to the database layer.

The service layer also coordinates data retrieval and prepares structured results for presentation. It does not contain SQL statements or directly manage database connections.

**Data Access Layer**

The data access layer is implemented through repository modules. Its responsibility is to encapsulate SQL statements and provide standardized interfaces for retrieving and modifying persistent data.

The current implementation contains three main repositories:

- `user_repository.py` handles user account retrieval and test-account listing.
- `category_repository.py` retrieves product categories and category information.
- `product_repository.py` implements product searching, filtering, pagination, product management, purchase operations, and purchase history retrieval.

All database operations are executed through the centralized connection factory in `database/connection.py`. This factory uses an absolute database path, enables SQLite foreign key enforcement through `PRAGMA foreign_keys = ON`, and configures `sqlite3.Row` as the query result format.

Parameterized SQL statements are used for user-provided query conditions, while sorting columns are selected from a predefined whitelist. This reduces the risk of SQL injection and ensures that database access follows consistent rules.

**Database Layer**

SQLite provides persistent storage for the three principal relational entities: `users`, `categories`, and `products`.

The database maintains relationships between users and products through seller and buyer identifiers, and between products and categories through category identifiers. Product transaction information is maintained directly within the product records using `buyer_id`, `status`, and `finished_at`.

By combining these layers, the architecture establishes a clear separation of responsibilities, improves code maintainability, and provides a structured foundation for database operations.

## 4.3 System Architecture Diagram

Figure 1 illustrates the overall architecture and the interactions between the user interface, business logic, repository modules, and SQLite database.

![](report/figures/Figure1_CampusMarket_Architecture.png)

The diagram illustrates the logical dependencies between application components. User requests are received by the Streamlit presentation layer and passed to the corresponding service functions. The service layer validates inputs and coordinates business operations before invoking repository interfaces. Repository modules execute SQL statements through the centralized database connection factory, which provides access to the SQLite database.

The architecture also ensures that database operations are not scattered across individual interface pages. For example, product searching and purchase history retrieval are both implemented in the repository layer, while their corresponding business logic is coordinated by `product_service.py`.

## 4.4 Functional Module Design

The application is organized into several functional modules, each responsible for a specific part of the marketplace workflow.

**Application and User Context Module**

The application entry point, `app.py`, initializes the Streamlit interface, configures page settings, displays an overview of the marketplace, and provides navigation to the functional pages.

User context management is implemented in `user_service.py`. The module retrieves predefined accounts from the user repository and stores the selected `user_id` in Streamlit session state. This allows the application to distinguish between different users when retrieving published products or purchase records.

**Marketplace Module**

The marketplace module is implemented in `pages/1_Marketplace.py` and supported by the product service and product repository.

It provides four main query dimensions: keyword, category, minimum price, and maximum price. Users can additionally select one of four sorting options: newest first, oldest first, lowest price first, and highest price first.

At the database level, the repository constructs SQL conditions dynamically while keeping user-supplied values in parameterized query arguments. Sorting expressions are selected through a predefined mapping rather than accepting arbitrary SQL input.

The module also implements pagination using `LIMIT` and `OFFSET`. A separate `COUNT(*)` query calculates the total number of matching products, allowing the interface to display the total number of results and the corresponding page information.

Only products with the `available` status are included in marketplace search results, ensuring that completed transactions are excluded from the active product listings.

**Product Detail and Management Module**

Product detail inspection is implemented in `pages/2_Product_Detail.py`. It retrieves product information using the product identifier and displays relevant attributes, including title, price, category, seller, description, publication time, and transaction status.

Product publishing and seller-side management are implemented in `pages/3_Sell_MyProducts.py`. The module allows users to create new listings, modify existing product information, and delete their own unsold products.

The corresponding service functions validate user input before invoking repository operations. Ownership restrictions are also enforced through database update and delete conditions that include both `product_id` and `seller_id`.

An important design consideration is the preservation of transaction records. Once a product has been sold, its transaction-related information must remain accessible. Therefore, the application prevents completed products from being deleted and does not allow ordinary product-editing operations to modify transaction-related fields such as `buyer_id`, `status`, and `finished_at`.

**Purchase and Transaction Module**

The purchase operation is integrated into the product detail page and implemented through `product_service.buy_product()` and `product_repository.buy_product()`.

The repository first checks whether the product exists, whether it is still available, and whether the current user is attempting to purchase their own listing. The purchase is then performed through a conditional SQL update:

```
UPDATE products
SET buyer_id = ?,
    status = 'sold',
    finished_at = ?
WHERE product_id = ?
  AND status = 'available';
```

The update is executed within a database transaction. The affected-row count is used to determine whether the purchase succeeds. If the update affects one row, the transaction has successfully changed the product's status. If no row is affected, the purchase is rejected because the product is no longer available.

This conditional update provides an important concurrency-control mechanism. Even if multiple users attempt to purchase the same product concurrently, only one operation can successfully change its status from `available` to `sold`. Subsequent attempts cannot satisfy the original availability condition.

Unlike conventional e-commerce applications, the current implementation does not maintain a separate `orders` table. Instead, the buyer identifier and transaction completion time are stored directly in the corresponding product record.

**Purchase History Module**

The purchase history functionality is implemented in `pages/4_My_Purchases.py`.

The module retrieves completed products associated with the current buyer through `get_my_purchases()`. The underlying repository query filters records using `buyer_id` and the `sold` status, joins the category table to retrieve category names, and orders the results by transaction completion time.

The interface presents several summary indicators, including the total number of purchased products, cumulative purchase amount, and most recent transaction date. It also supports category-based filtering and navigation back to the corresponding product detail page.

Following a successful purchase, the application uses Streamlit session state to retain the purchased product identifier and redirects the user to the purchase history page. This provides a continuous workflow from purchase execution to transaction record inspection.

## 4.5 User Workflow and Business Process

CampusMarket supports two primary user workflows: the seller workflow and the buyer workflow. Both workflows operate on the same relational database and are associated with the currently selected test account.

**Seller Workflow**

A seller first selects a predefined user account through the application sidebar. After entering the product management page, the seller can submit a new listing by providing the required product information, including its title, category, and price.

The service layer validates the submitted information before the repository inserts the new record into the `products` table. The newly published product is assigned the default `available` status.

The seller can subsequently retrieve all products associated with their `seller_id`, edit the information of their own listings, or delete products that have not been sold. Products with a completed transaction are retained in the database and cannot be deleted through the application interface.

**Buyer Workflow**

A buyer selects a test account and enters the marketplace page. The buyer can browse available products and narrow the results using keywords, categories, and price ranges. Sorting and pagination allow the buyer to navigate the resulting product listings.

After selecting a product, the buyer enters its detail page to inspect the product information and current transaction status. If the product remains available and the buyer is not its seller, the purchase operation can be initiated.

The system then executes the conditional update within a database transaction. Upon successful completion, the buyer identifier, sold status, and transaction completion timestamp are stored in the product record. The application subsequently redirects the buyer to the purchase history page, where the newly completed transaction is displayed.

If another user has already purchased the product, the conditional update affects zero rows and the application returns an appropriate failure message. This prevents the same product from being successfully purchased more than once.

The overall business process is illustrated in Figure 2.

![](report/figures/Figure2_Buyer_Transaction_Workflow.png)

The seller workflow operates independently through the product management module, while the buyer workflow illustrates the main transaction process. Both workflows share the same product records, allowing changes in product ownership and transaction status to be reflected consistently across the application.

## 4.6 Project Structure

The project adopts a modular directory structure that separates application pages, business logic, database access, database initialization, and supporting documentation.

The current project structure is organized as follows:

```
CampusMarket/
│
├── app.py
│
├── pages/
│   ├── 1_Marketplace.py
│   ├── 2_Product_Detail.py
│   ├── 3_Sell_MyProducts.py
│   └── 4_My_Purchases.py
│
├── services/
│   ├── user_service.py
│   └── product_service.py
│
├── repositories/
│   ├── user_repository.py
│   ├── category_repository.py
│   ├── product_repository.py
│   └── __init__.py
│
├── database/
│   ├── connection.py
│   ├── schema.sql
│   ├── seed.py
│   ├── patch_users.py
│   └── campus_market.db
│
├── tests/
│   ├── transactions/
│   └── functional/
│
├── docs/
│   ├── B_交接说明.docx
│   ├── 修改说明_20261119.docx
│   ├── 注意事项.docx
│   ├── C_Project_Audit.md
│   ├── C_Transaction_Test_Report.md
│   └── C_Integration_Report.md
│
├── report/
│   └── (final report sections)
│
├── check_interfaces.py
├── performance_test.py
├── test_repo.py
├── requirements.txt
├── README.md
└── .gitignore
```

The `app.py` file serves as the application entry point, while the `pages/` directory contains the individual Streamlit interfaces. The `services/` directory encapsulates application-level business rules and input validation, and the `repositories/` directory centralizes SQL queries and database operations.

The `database/` directory contains the SQLite database file, schema definition, and supporting database scripts. In particular, `connection.py` provides the centralized database connection interface used by repository modules. The existing database file is supplied with the project to ensure that the application can run against the prepared dataset without requiring users to regenerate the database.

The `docs/` directory stores development handover notes, integration documentation, and Member C's audit, test, and integration reports. In addition, `check_interfaces.py` provides an interface and integration verification mechanism, while `performance_test.py` and `test_repo.py` support database performance and repository-level testing. The `tests/` directory contains Member C's transaction, concurrency, integrity, and functional walkthrough suites, which run against isolated copies of the database.

This modular organization reflects the separation of concerns established by the three-layer architecture. It also facilitates parallel development and integration by allowing different team members to work on database design, application functionality, and transaction-related operations through clearly defined module interfaces.

---

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

---

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

---

# 7. Challenges and Lessons Learned

This section documents the challenges the team actually encountered during
the development of CampusMarket, how they were resolved in the delivered
code, and what we learned from them. All examples reference the real
artifacts in the project repository.

## 7.1 Database Schema Evolution: From a Separate Orders Table to Transaction State on Products

The earliest version of the database (2026-11-18) used four tables. Purchases
were recorded in a dedicated `orders` table, and the anti-oversell guarantee
was the `UNIQUE` constraint on `orders.product_id`: the database itself made
it impossible to create two purchase records for the same product. When the
dataset was regenerated (2026-11-19), the team removed the `orders` table and
moved the transaction state directly onto the product row through three
columns: `buyer_id`, `status` (`available`/`sold`), and `finished_at`.

This change had consequences beyond the DDL. The anti-oversell mechanism had
to be re-founded: a `UNIQUE` constraint no longer protects the workflow,
because the guard must now be expressed as a conditional
`UPDATE ... WHERE status = 'available'`. The user-facing repository functions
changed signature and semantics (for example, `get_my_purchases` now queries
`products` instead of an orders table). The handover documents from the
early version — including the statement that "the `UNIQUE` constraint on
`orders.product_id` is the bottom line against overselling" — became
obsolete and had to be explicitly marked as historical so that nobody
re-introduced the old model.

**Lesson:** a schema change is not a file change; it invalidates every
mechanism, document, and test built on the old model. The version that
finally ships must be identifiable from the repository itself, which is why
the delivered project keeps a single authoritative database file and
regenerates `schema.sql` from it.

## 7.2 Transaction and Concurrency: Making a Conditional UPDATE the Only Writer of a Sale

After the schema change, oversell prevention depends on the atomicity of one
statement:

```sql
UPDATE products
SET buyer_id = ?, status = 'sold', finished_at = ?
WHERE product_id = ? AND status = 'available';
```

A subtle defect existed in the first version of this interface: it executed
the conditional UPDATE but returned "purchase successful" without checking
the affected-row count. If a competing request committed its own update
between the pre-check (`SELECT status ...`) and the UPDATE, the second
request would affect zero rows yet still report success — a sale that never
happened would be acknowledged to the user. The merged repository fixed this
by wrapping the update in an explicit transaction (`with conn:`) and
deciding the outcome from `cur.rowcount`: zero affected rows means another
buyer won, and the interface returns the "already purchased by someone else"
message.

SQLite's rollback journal serializes writers, so the loser's UPDATE waits
on the write lock and then re-evaluates the `WHERE` clause against the
committed state. Member C verified this behavior with a genuine
multi-threaded test (`tests/transactions/test_concurrency.py`): two threads
synchronized on a `threading.Barrier` call the real `buy_product()`
concurrently; across 10 recorded rounds the result was always exactly one
success and one failure, with the winner alternating between threads and the
loser consistently showing a longer wait time. The sequence tests additionally
confirmed that duplicate purchases, self-purchases, and purchases of
nonexistent products all fail without side effects.

**Lesson:** correctness under concurrency must be judged from the database's
own evidence (affected-row count, final row state), never from the code path
taken; and a concurrency test that only replays sequential calls proves
nothing — the barrier-synchronized threads were necessary to exercise the
race at all.

## 7.3 Separation of Application Layers: SQL Stays in the Repository

The early delivery contained a corrupted connection string
(`sqlite3.connect('database/campus_market.dbpython test_repo.py')`) that
silently created an empty database file and produced "no such table"
errors. This motivated the unified connection factory
(`database/connection.py`): one absolute, file-relative path, `PRAGMA
foreign_keys = ON` on every connection, and `sqlite3.Row` rows. The delivered
project enforces a strict three-layer split — Streamlit pages contain no SQL
and no connections, services contain validation and orchestration only, and
all SQL lives in `repositories/`. A repository-level audit (text search and
AST cross-checking of page-to-service references) confirmed the boundary
holds in the delivered code.

The split also shaped the interface contract. When the application needed new
queries, the pages could not simply add ad-hoc SQL; the data access layer
grew explicit functions instead. Two details are deliberate: sorting
expressions are chosen from a whitelist mapping (never string-concatenated
from user input), and product editing/deletion always includes `seller_id`
in the `WHERE` clause so ownership is enforced at the database level.

**Lesson:** layer separation is less about style than about where defects can
happen. Centralizing connections fixed a real bug class (path corruption,
forgotten foreign keys), and confining SQL made injection-safety review a
single-file task.

## 7.4 Data Integrity and Consistency: Constraints Must Be Turned On, Not Just Written

Three integrity-related incidents shaped the delivered design.

First, the early seed script had an indentation bug that left the `users`
table with a single row while products referenced seller IDs 1–100, so
foreign-key violations blocked every publish operation once foreign keys
were enabled; a remediation script had to backfill 99 accounts, and the
regenerated baseline (1,000 users) made the problem disappear.

Second, SQLite's `PRAGMA foreign_keys` is off by default **per connection**
and is not persisted in the file. Writing `FOREIGN KEY` clauses in the DDL
is therefore not enough; the connection factory enables the pragma on every
connection it returns, and the integration self-check asserts this. Member
C's tests inject invalid buyer/seller/category references and negative
prices into an isolated copy and verify each is rejected with an
`IntegrityError`.

Third, integrity extends to the workflow: a sold product's transaction
record must survive. The application blocks deletion of sold products (the
service layer raises a validation error and the page hides the delete
button), and the integrity tests check both directions of the status
invariant — every sold row has `buyer_id` and `finished_at`, every available
row keeps them NULL — against the full 10,000-row baseline and against a
post-purchase copy.

**Lesson:** declarative constraints only protect the system when the runtime
configuration (per-connection pragmas) and the business rules (what may be
deleted) are aligned with them — and when tests actually provoke the
violations instead of assuming they are impossible.

## 7.5 Team Collaboration and Integration: Merge, Do Not Replace

The integration step between Member A's database update and Member B's
application was the highest-risk moment of the project. A's update note said
to "directly replace the two same-named files." Doing so would have deleted
seven functions of B's repository layer (filter building, pagination,
counting, publish/edit/delete), immediately breaking the marketplace and
seller pages. B merged instead: A's new interfaces (`buy_product`,
`get_my_purchases`) were incorporated into the existing repository, adapted
to the unified connection factory and transaction boundary, and the new
database file was swapped in with a regenerated `schema.sql`.

The integration was then made verifiable rather than assumed: a read-only
self-check script (`check_interfaces.py`) asserts the model (three tables,
no `orders`), the fields, the data snapshot, foreign-key cleanliness, and
that A's performance script still runs. Handover documents recorded the data
snapshot (users/categories/products counts) and the do-not-run list (the
obsolete seed script would collide with the dataset if re-executed). A later
audit by Member C found one documentation/data mismatch — three products
purchased during a verification session were not restored, so the
available/sold split is 3,961/6,039 rather than the documented 3,964/6,036
while all totals agree — which was resolved by correcting the documented
figures rather than by touching the baseline database.

**Lesson:** when two members' deliverables overlap in one file, "replace" is
almost always the wrong verb; merge against an explicit interface contract,
and give the team a script that can re-verify the contract at any time.

## 7.6 Testing and Validation: Layered Evidence Instead of a Single Test

The project ended up with four complementary levels of verification, each
added by the member best placed to write it: A's index performance experiment
(with/without index timing and `EXPLAIN QUERY PLAN`), B's read-only
integration self-check of the model and interface contract, and Member C's
unittest suites — transaction semantics, multi-threaded oversell racing, and
integrity/constraint injection, all running on byte-copied database
instances with the repository connection factory redirected to the copy, so
the 10,000-product baseline is never written by a test. A final
service-level walkthrough replays the exact page call sequence from
publishing to purchase history.

Two practical lessons emerged from building the test environment. Replacing
the connection factory requires patching the name inside each repository
module (they import `get_connection` directly), not only the definition
module — the task looks symmetrical but is not. And test isolation needs a
tamper-evident guarantee: every test teardown re-hashes the baseline
database and fails if one byte changed, which turned "we were careful" into a
checkable property.

**Lesson:** each layer of the system needs its own falsifiable evidence;
when a layer cannot be exercised directly (in our case, Streamlit rendering
in a headless environment), state that limitation explicitly rather than
inferring the result from unrelated checks.

---

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

**In-text citation mapping**

| Report location | Reference(s) |
| --- | --- |
| Connection factory: `PRAGMA foreign_keys`, `sqlite3.Row` (§4.2, §7.3, §7.4) | 1, 6 |
| Purchase transaction and conditional UPDATE (§4.4, §7.2) | 1, 7 |
| Concurrency design and lock serialization; concurrency test (§4.4, §7.2, §7.6) | 2, 8 |
| Test suite construction (§7.6) | 3 |
| Test-account session context and page navigation (§3.4, §4.4) | 4, 5 |

---

# 9. Links to Deliverables

The deliverables for this project consist of the CampusMarket application
repository, the final report (this document), and an English demonstration
video of 5–8 minutes recorded against the running application.

## 9.1 Source Code Repository

- GitHub repository: https://github.com/logic66-luoji/CampusMarket (private;
  access to be granted to the course instructor)

  The repository contains the complete application (`app.py`, `pages/`,
  `services/`, `repositories/`), the SQLite database and schema
  (`database/`), the test suites (`tests/transactions/`,
  `tests/functional/`), the project reports (`docs/`), and this report
  (`report/`). The database baseline file is intentionally included in the
  repository so that the application runs without a data regeneration step.

## 9.2 Video Demonstration

- Demonstration video: [Insert demonstration video URL]

  The video follows the script in `presentation/Video_Script.md` and the
  operating checklist in `presentation/Demo_Checklist.md`: system
  architecture, product browsing and filtering, seller operations, the
  complete purchase workflow (including the duplicate-purchase rejection and
  the purchase history redirect), the database design, and the transaction
  and concurrency test results.

## 9.3 Supplementary In-Repository Documents

| Deliverable | Location |
| --- | --- |
| Member C project audit report | `docs/C_Project_Audit.md` |
| Transaction and concurrency test report | `docs/C_Transaction_Test_Report.md` |
| Concurrency run evidence (raw data) | `tests/transactions/results/concurrency_runs.json` |
| System integration report | `docs/C_Integration_Report.md` |
| Report source sections | `report/` |
| Video script and demonstration checklist | `presentation/` |

> Note: the repository URL above is final. The video URL remains a
> placeholder until the recording is uploaded; no URLs have been fabricated.

---

*End of report. Consolidation and consistency check by Member C,
2026-11-21.*
