# C_Transaction_Test_Report — 事务与并发测试报告

- 编写人：Member C
- 日期：2026-11-21
- 测试代码：`tests/transactions/`（test_purchase.py / test_concurrency.py / test_integrity.py / testenv.py）
- 结论先行：**11 项测试全部通过**；并发竞争 10 轮均「恰好一胜一负」；原始基准库全程零写入（SHA-256 复核不变）。

---

## 1. 测试环境（真实环境信息）

| 项目 | 值 |
| --- | --- |
| 操作系统 | Windows 10（10.0.22621，64 位） |
| Python | 3.10.0 |
| SQLite 版本 | 3.35.5（Python 标准库 sqlite3） |
| 测试框架 | unittest（标准库）＋ threading / sqlite3，无第三方新依赖 |
| 被测数据库 | `database/campus_market.db`（2,117,632 字节；users 1,000 / categories 5 / products 10,000） |
| 日志模式 | `journal_mode=delete`（回滚日志，SQLite 默认） |
| 运行方式 | `python tests/transactions/test_<x>.py` 或 `python -m unittest discover -s tests`（两种方式均已实跑） |

**隔离原则：** 每个测试用例先把基准库按字节复制到 `tests/transactions/.tmp/` 下的临时副本，再把 `product_repository` / `user_repository` / `category_repository`（及 `database.connection`）模块内实际引用的 `get_connection` 替换为指向副本的同约定工厂。**被测业务代码（buy_product 等）一字未改**；tearDown 恢复原工厂、删除副本，并断言基准库 SHA-256 恒等于
`d92adc770fed9df9e30d58944a7ecd7c18f3cc40a1fc244cf90f101337245fdd`。
（`product_repository.py` 采用 `from database.connection import get_connection` 名字绑定导入，因此必须逐模块替换，仅改 `database.connection` 无效——这正是任务书提示的坑。）

## 2. 测试方法

| 测试 | 方法概要 |
| --- | --- |
| Test 2.1 正常购买 | 副本中以真实 `create_product()` 发布在售商品 → service 层 `ps.buy_product()` 购买 → 断言返回「购买成功！」、`buyer_id/status/finished_at` 三字段、`get_my_purchases` 命中且带分类名、卖家视角 `get_user_products` 状态同步 |
| Test 2.2 重复购买 | 成交后另一买家与原买家各再购一次 → 断言均返回「已被抢先买走」、原买家/成交时间不变、败者历史无记录、成交记录仍仅 1 条 |
| Test 2.3 自购 | 卖家购买自己的 available 商品 → 断言拒绝、整行数据与购买前逐字段相等 |
| Test 2.4 不存在商品 | `product_id=999999999` → 断言返回「商品不存在」、商品总数与 sold 数不变、无残行 |
| Test 2.5 并发购买 | 每轮副本内发布一件 available 商品；两个买家线程经 `threading.Barrier` 同步后**同时**调用真实 `buy_product()`；断言成功数=1、失败数=1、终态 sold、`buyer_id`=胜者、成交时间非空、胜者历史含该商品且败者不含；共 10 轮 |
| Test 2.6 完整性 | A：基准库以 `mode=ro` 只读 URI 执行 10 条规则 + `PRAGMA foreign_key_check`；B：副本真实购买后复查全部规则；注入非法 status / 负价格 / 无效外键须 `IntegrityError`；模拟「只改 status 不清 buyer_id」的绕过篡改必须被规则捕获 |

## 3. 测试数据

- 基底：A 交付的 2026-11-19 基准库副本（10,000 商品 / 1,000 用户）。
- 每个用例经真实发布接口在副本中新建测试商品（product_id 自 10,001 起），卖家 user_id=1，买家 user_id=2、3（均为库中既有账号，不新增用户）。
- 未触碰原始 10,000 行商品数据；所有写入只发生在副本。

## 4. 实测结果（2026-11-21 实跑记录）

### 4.1 顺序功能测试（test_purchase.py）— 4/4 通过

```
test_buy_nonexistent_product_reports_error_and_changes_nothing ... ok   (Test 2.4)
test_buy_available_product_succeeds_and_records_transaction   ... ok   (Test 2.1)
test_second_purchase_fails_and_keeps_first_transaction        ... ok   (Test 2.2)
test_seller_cannot_buy_own_product                            ... ok   (Test 2.3)
Ran 4 tests in 0.092s — OK
```

### 4.2 并发购买测试（test_concurrency.py）— 2/2 通过，10 轮竞争明细

```
test_exactly_one_buyer_wins_each_round ... ok
test_losers_message_after_race_is_sniped ... ok
Ran 2 tests in 0.335s — OK
```

10 轮明细（摘自 `results/concurrency_runs.json`，全部为真实运行数据）：

| 轮次 | product_id | 胜者 | 败者提示 | 成功/失败 | 终态 status / buyer_id / finished_at | 胜者耗时 | 败者耗时 |
| ---: | ---: | ---: | --- | :-: | --- | ---: | ---: |
| 1 | 10001 | buyer#3 | 已被抢先买走 | 1 / 1 | sold / 3 / 非 NULL | 6.57 ms | 16.44 ms |
| 2 | 10002 | buyer#2 | 已被抢先买走 | 1 / 1 | sold / 2 / 非 NULL | 12.25 ms | 21.07 ms |
| 3 | 10003 | buyer#3 | 已被抢先买走 | 1 / 1 | sold / 3 / 非 NULL | 10.69 ms | 16.45 ms |
| 4 | 10004 | buyer#3 | 已被抢先买走 | 1 / 1 | sold / 3 / 非 NULL | 7.22 ms | 12.25 ms |
| 5 | 10005 | buyer#3 | 已被抢先买走 | 1 / 1 | sold / 3 / 非 NULL | 10.31 ms | 12.57 ms |
| 6 | 10006 | buyer#2 | 已被抢先买走 | 1 / 1 | sold / 2 / 非 NULL | 8.89 ms | 23.56 ms |
| 7 | 10007 | buyer#3 | 已被抢先买走 | 1 / 1 | sold / 3 / 非 NULL | 10.32 ms | 12.88 ms |
| 8 | 10008 | buyer#2 | 已被抢先买走 | 1 / 1 | sold / 2 / 非 NULL | 10.63 ms | 11.72 ms |
| 9 | 10009 | buyer#2 | 已被抢先买走 | 1 / 1 | sold / 2 / 非 NULL | 10.24 ms | 25.35 ms |
| 10 | 10010 | buyer#2 | 已被抢先买走 | 1 / 1 | sold / 2 / 非 NULL | 9.14 ms | 12.70 ms |

**汇总：** 10 轮 × 2 线程 = 20 次购买请求；成功 10 次、失败 10 次；每轮成功数与失败数均恰好为 1；无任何线程异常或「database is locked」错误。胜负分布 buyer#2 五轮、buyer#3 五轮——胜者并非固定线程，证明竞争是真实发生并被数据库锁与条件 UPDATE 串行化裁决的（败者耗时普遍长于胜者，即败者在写锁上等待后命中 `WHERE status='available'` 的 0 行更新）。

### 4.3 数据完整性测试（test_integrity.py）— 5/5 通过

```
test_baseline_history_satisfies_all_rules          ... ok   基准库 10 条规则 0 违规 + foreign_key_check 0 处
test_check_constraints_reject_invalid_status_and_price ... ok   非法 status / 负价格 → IntegrityError
test_foreign_keys_reject_invalid_references        ... ok   无效 seller/category/buyer 引用 → IntegrityError
test_rules_catch_bypassed_tampering_then_recover   ... ok   半吊子篡改被规则捕获，完整还原后归零
test_rules_hold_after_real_purchase_flow           ... ok   真实购买流程后全部规则仍 0 违规
Ran 5 tests in 0.124s — OK
```

### 4.4 汇总

| 套件 | 通过 / 总数 | 结果 |
| --- | :-: | --- |
| test_purchase.py | 4 / 4 | OK |
| test_concurrency.py | 2 / 2 | OK |
| test_integrity.py | 5 / 5 | OK |
| **合计** | **11 / 11** | **OK**（discovery 模式与单文件模式均复跑通过） |

## 5. 数据库状态验证

- 原始基准库：每个 tearDown 强制断言 SHA-256 == `d92adc77…37245fdd`；测试后人工复验一致 → **测试未破坏原始数据库**。
- 临时副本：每用例结束即删除（`tests/transactions/.tmp/` 仅保留空目录壳）。
- 商品总数恒为 10,000：副本测试新增的行（10,001 起）随副本一并销毁。

## 6. 测试结论

1. **防超卖机制成立。** `buy_product()` 的三重前置校验（存在 / 未售 / 非自购）＋单事务条件 `UPDATE ... WHERE status='available'` ＋ rowcount 判定，在真实多线程竞争下保证了同一商品恰好一次成交；该保证来自数据库原子性而非应用层约定。
2. **事务边界正确。** 失败路径（重复购买、自购、不存在商品）零副作用；成功路径三字段（`buyer_id`、`status`、`finished_at`）同事务写入，无中间态残留。
3. **约束体系有效。** CHECK（价格、状态）与外键（开启 `PRAGMA foreign_keys` 的连接）在注入测试中全部拒绝非法数据；完整性规则能够捕获绕过业务层的篡改。
4. **历史数据合规。** 基准库在 10 条一致性规则与外键检查上 0 违规（known issue：available/sold 计数与文档口径差 3 件，属测试遗留数据，见 `docs/C_Project_Audit.md` §6.1，与本测试无关）。
5. 以上所有数字均来自 2026-11-21 在上述环境的真实运行，明细文件为 `tests/transactions/results/concurrency_runs.json`。

## 7. 局限说明（如实记录）

- 并发竞争依赖线程调度，10 轮全部触发真实竞争；轮数可通过 `test_concurrency.py` 中 `ROUNDS` 调整。
- 测试在 Python 3.10.0 / SQLite 3.35.5 环境完成；不同 SQLite 版本的 busy-timeout 行为一致（默认 5 s），结论可复现。
- 本报告不涉及性能压测（吞吐/TPS），A 的 `performance_test.py`（索引前后对比）属 §6 评估范畴，二者互补不重叠。
