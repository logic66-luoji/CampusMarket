# 3. Project Overview

**Problem statement.** Campus second-hand trading typically happens through informal chat groups, where product information is unstructured, searches are manual, and completed transactions leave no reliable record. Information about users, categories, products, and purchases must stay mutually consistent — in particular, the same item must never be sold twice, and sellers must not be able to alter or erase completed sales.

**Application goals.** CampusMarket provides a centralized web platform that (1) organizes users, categories, and products in a relational database with primary keys, foreign keys, and CHECK constraints; (2) supports keyword search, category and price-range filtering, whitelist sorting, and pagination over available products; (3) lets users publish, edit, and delete their own listings while preserving sold-product records; (4) records purchases as exactly-once transactions; and (5) demonstrates a maintainable three-layer separation of presentation, business logic, and data access.

**Target users.** University students buying and selling second-hand goods on campus. For demonstration purposes the current scope uses predefined test accounts switched in the sidebar instead of a registration/password system; payment, logistics, and reviews are out of scope.
