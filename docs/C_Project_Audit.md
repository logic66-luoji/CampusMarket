# C_Project_Audit — CampusMarket 交接验收审计报告

- 编写人：Member C
- 日期：2026-11-21
- 审计对象：Member A 与 Member B 已交付的 CampusMarket 工程（以 `CampusMarket.zip` 内的最终整合工程为基准）
- 审计方式：只读检查（数据库以 `mode=ro` URI 打开；未对原始 `database/campus_market.db` 做任何写入）

---

## 1. 审计结论（TL;DR）

**A、B 交付的工程可以验收。** 数据库三张核心表、约束、索引、数据规模与文档一致（个别统计口径除外，见 §6.1）；三层架构边界清晰；`check_interfaces.py` 9/9 通过；A 的两个脚本可运行；购买接口三层贯通且防超卖逻辑正确。

未发现需要修改 A、B 代码的缺陷。C 阶段全部工作（事务/并发测试、报告、视频）均为**纯增量**，不改动 A、B 既有文件。

---

## 2. 各成员已完成工作梳理

### 2.1 Member A（数据库域）

| 交付物 | 状态 | 说明 |
| --- | --- | --- |
| 关系模式与 `schema.sql` | ✅ 有效 | 最终三表模型：`users` / `categories` / `products`；主键、外键、CHECK 齐全 |
| `campus_market.db`（2026-11-19 重新交付） | ✅ 基准库 | 1,000 用户 / 5 分类 / 10,000 商品，含 `buyer_id`、`finished_at`、available/sold 双状态 |
| `repositories/product_repository.py`（更新包） | ⚠️ 已被合并 | A 更新包版含 `buy_product` / `get_my_purchases`，但其 `get_connection()` 未开启外键、路径为相对路径；B 已合并进统一连接工厂 |
| `performance_test.py` | ✅ 可运行 | 实测：有索引 ~0 ms、全表扫描 ~11.9 ms，`EXPLAIN QUERY PLAN` 确认走 `idx_products_category_status` |
| `test_repo.py` | ✅ 可运行 | 见 §6.4：旧关键词「的」在新文案下命中 0 条（数据口径漂移，非代码缺陷） |
| `database/seed.py` | 🗄️ 留档 | 早期造数脚本（仅 100 用户、无 buyer_id/finished_at），**禁止重跑**（B 已在文件头加注） |
| `database/patch_users.py` | 🗄️ 留档 | 早期库补账号脚本，已加防护（用户数 ≥ 1000 时直接返回） |
| 早期 `docs/注意事项.docx` | 🗄️ 已过时 | 描述的是 2026-11-18 四表模型（orders 表 + product_id UNIQUE 防超卖），**不再适用**，仅作历史参考 |

A 早期版本的连接串 bug（`sqlite3.connect('database/campus_market.dbpython test_repo.py')`）与 `seed.py` 用户 INSERT 缩进 bug 均已在 2026-11-19 更新包 / B 的 P0 阶段修复，不构成当前问题。

### 2.2 Member B（应用域）

| 交付物 | 状态 | 说明 |
| --- | --- | --- |
| `database/connection.py` | ✅ | 统一连接工厂：基于 `__file__` 的绝对路径、每连接 `PRAGMA foreign_keys = ON`、`row_factory = sqlite3.Row` |
| `repositories/product_repository.py`（合并版） | ✅ | 保留 B 的 P1 能力（筛选/白名单排序/分页/发布/编辑/删除）并合入 A 的购买接口；购买改写为单个 `with conn:` 事务 + 条件 UPDATE + rowcount 判定 |
| `repositories/{user,category}_repository.py` | ✅ | 只读接口，SQL 全部集中于 repositories/ |
| `services/{product,user}_service.py` | ✅ | 参数校验、筛选组装、购买编排；零 SQL、零连接 |
| `pages/` 四个业务页 + `app.py` | ✅ | 商品广场 / 详情购买 / 发布管理 / 我的购买；已售商品隐藏删除按钮、购买成功跳转购买历史 |
| `check_interfaces.py` | ✅ | 9/9 通过（见 §4） |
| `README.md`、`requirements.txt`、`.gitignore` | ✅ | 数据库文件刻意不进 `.gitignore`（基准快照），符合项目定位 |
| `docs/B_交接说明.docx`（v3） | ✅ | 与代码现状一致，明确 C 的剩余工作 |

### 2.3 版本演进确认（防止误用旧说明）

```
2026-11-18  A 早期版：users/categories/products/orders 四表
            orders.product_id UNIQUE 为防超卖底线；users 仅 1 行（seed 缩进 bug）
    ↓  A 更新包（2026-11-19）
2026-11-19  A 更新版：orders 移除，products 增加 buyer_id/finished_at，
            buy_product/get_my_purchases 并入 product_repository.py
    ↓  B 合并（2026-11-19）
当前基准：  三表模型 + 统一连接工厂 + B 的筛选/分页/发布/编辑/删除 + A 的购买接口
            v3 再补 pages/4_My_Purchases.py 购买闭环
```

**结论：一切以 `CampusMarket.zip` 为准。** A 的「直接替换两个同名文件」的说明不能照做（B 已按合并处理，保留 P1 的 7 个函数），早期 `注意事项.docx` 中「orders 表 product_id UNIQUE 是防超卖底线」的表述已失效，最终报告中不得再出现。

---

## 3. 当前项目结构（审计时点）

```text
CampusMarket_Final/                ← B 工程原样副本 + C 增量交付
├── app.py                         B  主入口
├── pages/                         B  4 个业务页
├── services/                      B  业务层（零 SQL）
├── repositories/                  B+A合并  数据访问层（SQL 只在此）
├── database/
│   ├── connection.py              B  统一连接工厂
│   ├── schema.sql                 A  与 .db 一致的 DDL（已核对，见 §5.3）
│   ├── seed.py / patch_users.py   A  留档，禁止重跑
│   └── campus_market.db           A  基准快照（本审计全程只读）
├── performance_test.py            A  索引性能实验
├── test_repo.py                   A  早期数据访问自测
├── check_interfaces.py            B  联调自检
├── tests/transactions/            C  事务与并发测试（Phase 2 新增）
├── docs/                          B 的 3 份 docx + C 的 3 份报告（新增）
├── report/                        C  报告 Section 1/2/7/8/9 + Final_Report（新增）
├── presentation/                  C  视频讲稿与演示清单（新增）
├── requirements.txt               B
├── README.md                      B（C 附最终交付说明）
└── .gitignore                     B
```

---

## 4. 已通过的检查项

### 4.1 `check_interfaces.py`（B 的只读自检，实跑）

```
[PASS] 统一连接开启外键: foreign_keys=1
[PASS] 三张核心表齐全且 orders 已移除: categories, products, sqlite_sequence, users
[PASS] 成交字段 buyer_id / finished_at 存在
[PASS] status 同时含在售与已售: {'available': 3961, 'sold': 6039}
[PASS] 数据快照符合队友交付: {'users': 1000, 'categories': 5, 'products': 10000}
[PASS] 外键完整性: 0 处违规
[PASS] 商品详情字段完整
[PASS] 购买接口可调用: buy_product(product_id, buyer_id) -> 'str'
[PASS] A 的 performance_test.py 可运行: exit=0
结果：9/9 通过
```

### 4.2 C 补充的只读审计（实跑脚本 + 静态检查）

| # | 检查项 | 结果 |
| --- | --- | --- |
| 1 | 三张核心表存在、`orders` 已移除 | ✅（`sqlite_sequence` 为 AUTOINCREMENT 系统表，属预期） |
| 2 | 记录数 users=1000 / categories=5 / products=10000 | ✅ |
| 3 | 主键 / 外键 / CHECK 约束定义与 `schema.sql` 完全一致 | ✅ DDL 逐字符比对通过 |
| 4 | `PRAGMA foreign_keys` 经连接工厂开启 | ✅（SQLite 该 PRAGMA 不落盘、按连接生效，工厂是唯一入口，符合预期） |
| 5 | `PRAGMA foreign_key_check` 违规数 | ✅ 0 |
| 6 | 索引 `idx_products_buyer`、`idx_products_category_status` 存在 | ✅ |
| 7 | 数据库连接路径（基于 `__file__` 绝对路径，任意 cwd 可用） | ✅ |
| 8 | 三层职责分离：pages/services 中无任何 SQL/连接（grep 实证） | ✅ |
| 9 | pages 引用的全部 `ps.*` 接口在 services 中真实存在（AST 解析） | ✅ |
| 10 | 全工程 `py_compile` | ✅ ALL OK |
| 11 | Service 层冒烟（CLI fallback）：筛选/校验/详情/购买历史/发布商品列表 | ✅ |
| 12 | 自购拦截（available 自有商品，购买前记录 == 购买后记录） | ✅ 拒绝且数据不变 |
| 13 | `performance_test.py` 实跑 | ✅ 索引 0.00 ms vs 全表 11.87 ms，执行计划确认用索引 |
| 14 | `test_repo.py` 实跑 | ✅ 可运行（关键词命中率问题见 §6.4） |

---

## 5. 数据库实际状态（2026-11-21 只读核实）

| 项目 | 实测值 | 交接文档口径 | 判定 |
| --- | ---: | ---: | --- |
| users | 1,000 | 1,000 | 一致 |
| categories | 5 | 5 | 一致 |
| products 总数 | 10,000 | 10,000 | 一致 |
| available | **3,961** | 3,964 | **差 3，见 §6.1** |
| sold | **6,039** | 6,036 | **差 3，见 §6.1** |
| 外键违规 | 0 | 0 | 一致 |
| 索引 | 2 个 | 2 个 | 一致 |
| journal_mode | delete（回滚日志） | 未记载 | 并发测试需关注，见 §6.5 |

数据一致性规则实测（全部 0 违规）：

- 已售商品必有 `buyer_id` 与 `finished_at`：违规 0
- 在售商品 `buyer_id` 与 `finished_at` 保持 NULL：违规 0
- 无无效 `seller_id` / `buyer_id` / `category_id`：违规 0
- 无「购买自己商品」的历史成交：0
- 无非法 `status` 值、无负价/空价：0

---

## 6. 发现的问题（按四类区分）

### 6.1 文档描述不一致 —— available/sold 分布与基准快照差 3 件

**现象：** 全部交接文档（B 交接说明、check_interfaces 预期、任务书）记载 available=3,964 / sold=6,036，实测为 3,961 / 6,039。

**溯源（只读查询实证）：** product_id **6578、9777、4610** 三行 `buyer_id=1`、`finished_at` 分别为 `2026-11-19 10:40:10 / 10:40:46 / 11:33:26`。基准库合成数据的时间戳均带 `:24:02` 秒特征，这三行是 2026-11-19 B 做 v3 购买闭环验证时（「购买成功 → 再买被拒 → 查记录 → 恢复原值」）产生的**真实购买**，其中三次购买未恢复原值。属**测试遗留数据，非代码缺陷**。

**分类：** 文档描述不一致 + 测试遗留数据。

**影响评估：**
- 三表总数、外键、索引、CHECK 全部不受影响；A 的 §6 索引实验基准（10,000 行）不受影响；
- `check_interfaces.py` 只校验总数，不校验 available/sold 分布，因此 9/9 通过与该差异并存；
- 若不处理，报告 §6.1 数据集描述与实库会差 3 件。

**处置建议（C 不擅自修库）：**
1. 交由 A/B 决定：要么在文档口径上统一为实测值 3,961/6,039（推荐，零风险），要么由 B 用其备份回滚这 3 行（C 不执行）。
2. C 的最终报告一律采用**实测值**并注明口径；不写 3,964/6,036。

### 6.2 测试环境问题 —— 本环境无法启动 Streamlit

**现象：** C 的执行环境为 Python 3.10.0，未安装 `streamlit`；按任务约束「全过程不下载任何应用或软件」，不能 `pip install`。

**分类：** 测试环境问题，非代码缺陷。

**已做的替代验证：** 全部 5 个页面 `py_compile` 通过；pages 对 services 的全部引用经 AST 解析一一存在；service 层 CLI 冒烟（user_service 自带无 Streamlit 的 fallback）全部通过；B 的 v3 验证快照记载「五个页面 AppTest 执行无异常、无头启动 health 200」，作为其环境下的遗留证据引用。**Streamlit 实际启动验证留待有完整依赖的环境执行**（`pip install -r requirements.txt && streamlit run app.py`），已列入视频演示前置条件。

> **后续更新（2026-11-21）：** 经授权安装 streamlit 1.65.0 后，本项已在隔离验证副本上完成实机验收（四页面 + 购买闭环 + 自购拦截 + 已售禁删全部通过，截图存档 `presentation/screenshots/`）。详见 `docs/C_Integration_Report.md` §5.1。

### 6.3 非必要的优化建议（不执行，仅记录）

- `requirements.txt` 中 `pandas` 与 `Faker` 在应用代码中无 import（前者为数据脚本预留、后者仅 `seed.py` 使用）。按「控制修改范围」原则**保留不动**，避免影响 A、B 的 §6 脚本与既有 README 口径。
- `user_repository.list_test_users` 侧边栏仅列前 100 个账号（`MAX_TEST_USERS=100`），属有意裁剪，无需改。
- `users.password_hash` 字段存在但本期不做认证——为已声明的范围裁剪（报告 §3.4/§7 口径），不是缺陷。

### 6.4 数据口径漂移 —— A 的 `test_repo.py` 关键词失效

`test_repo.py` 用关键词「的」搜索，在 2026-11-19 之前的 Faker 随机长句文案下可命中；新库为简洁校园文案（如「高数教材第七版」），命中 0 条。脚本仍可正常运行（详情查询正常返回）。**按约束不改 A 的脚本**，仅记录：演示与功能验证改用新库真实关键词（鼠标 / 教材 / 牛仔裤 / 哑铃 实测各命中 20+ 条）。

### 6.5 并发测试环境备注（供 Phase 2 使用）

`journal_mode` 为默认 `delete`（回滚日志）。两线程并发写同一行时，SQLite 通过写锁 + busy timeout（Python 默认 5 s）串行化；`buy_product` 的条件 `UPDATE ... WHERE status='available'` 在锁释放后重新执行，恰好一胜一负。该机制正是 Test 2.5 要实证的对象。

---

## 7. 需要 C 进一步处理的事项（本审计后的工作清单）

| # | 事项 | 状态 |
| --- | --- | --- |
| 1 | `tests/transactions/`：正常购买 / 重复购买 / 自购 / 无效商品 / 并发 / 完整性 六项测试（隔离副本上运行） | Phase 2 |
| 2 | `docs/C_Transaction_Test_Report.md`：真实运行结果 | Phase 2 |
| 3 | 系统整合核查 + `docs/C_Integration_Report.md`（记录 C 的全部增量与未决项） | Phase 3 |
| 4 | 报告 Section 1/2/7/8/9 + 全文统稿 `Final_Report.md`（§6.1 的口径问题在统稿时对 A 提出明确修改请求） | Phase 4 |
| 5 | 视频讲稿 + 演示清单（购买闭环演示按 B 交接 §5.1 的路线） | Phase 5 |

---

## 8. 审计期间的完整性保证

- 原始库 `database/campus_market.db` 以只读 URI 打开；审计前后 SHA-256 均为
  `d92adc770fed9df9e30d58944a7ecd7c18f3cc40a1fc244cf90f101337245fdd`（未变）。
- 审计期间对工程文件零修改；本报告与 `tests/`、`report/`、`presentation/` 为纯新增文件。
- B 工程基线的 27 个文件 SHA-256 清单存于 `baseline_B_project.sha256`，供 Phase 6 终验比对。
