# C_Integration_Report — 系统整合与最终验收报告

- 编写人：Member C
- 日期：2026-11-21
- 性质：Phase 3 功能整合记录。**A、B 既有代码零修改**，C 的全部工作为新增文件 + 本报告所列文档级增补。

---

## 1. 整合范围与结论

在 `docs/C_Project_Audit.md` 审计通过的基础上，Phase 3 完成了：

1. **接口自检复跑**：`python check_interfaces.py` → 9/9 通过（见 §2.1）。
2. **A 的脚本复跑**：`performance_test.py`（索引对比 + 执行计划）与 `test_repo.py` 均可运行（见 §2.2）。
3. **完整功能验证**：新增 `tests/functional/test_workflow_integration.py`，按四个 Streamlit 页面的真实调用序列在隔离副本上走通全部用户旅程 → 13/13 全套件通过（含 Phase 2 的 11 项，见 §3）。
4. **静态整合检查**：三层边界、依赖清单、README 结构、orders 遗留物（见 §4）。
5. **兼容性记录**：发现 1 处行为顺序细节与 3 项环境/口径事项，均无需改 A、B 代码（见 §5）。

## 2. 已有自检与脚本实跑结果

### 2.1 `python check_interfaces.py`（B 的只读自检）

```
[PASS] 统一连接开启外键: foreign_keys=1
[PASS] 三张核心表齐全且 orders 已移除
[PASS] 成交字段 buyer_id / finished_at 存在
[PASS] status 同时含在售与已售: {'available': 3961, 'sold': 6039}
[PASS] 数据快照符合队友交付: {'users': 1000, 'categories': 5, 'products': 10000}
[PASS] 外键完整性: 0 处违规
[PASS] 商品详情字段完整
[PASS] 购买接口可调用
[PASS] A 的 performance_test.py 可运行: exit=0
结果：9/9 通过
```

### 2.2 A 的脚本

- `performance_test.py`：实跑通过。索引查询 ~0 ms，去索引全表扫描 ~11.9 ms，`EXPLAIN QUERY PLAN` 输出 `SEARCH products USING INDEX idx_products_category_status`，可直接用于 A 的报告 §6.3/§6.4。
- `test_repo.py`：可运行；详情查询正常，关键词「的」在新文案数据下命中 0 条（数据口径漂移，见 C_Project_Audit §6.4，非缺陷）。

## 3. 完整功能验证（C 新增 `tests/functional/`）

**定位说明：** 不重复 B 的 `check_interfaces.py`（数据模型/接口契约只读自检）。`tests/functional/test_workflow_integration.py` 按 **页面真实调用序列** 走通业务旅程，补上「服务层端到端」这一层验证。两者互补。

### 3.1 用例 `test_publish_browse_detail_buy_history_manage`

按页面顺序逐步执行（隔离副本，业务代码零改动）：

| 页面 | 验证点 | 结果 |
| --- | --- | --- |
| app.py 侧边栏 | `set_current_user` / `get_current_user` 切换与保持 | ✅ |
| 3_Sell 发布 | `publish_product` 校验 + 落库，返回新 product_id | ✅ |
| 1_Marketplace | 关键词命中；价格区间 + 「价格从高到低」排序正确；越界页码收敛 | ✅ |
| 2_Detail | `get_product` 详情字段完整，初始 available | ✅ |
| 购买 | 自购被拒（ok=False）；买家购买成功 | ✅ |
| 4_My_Purchases | `get_my_purchases` 含该笔成交；详情页转 sold + buyer_id + finished_at | ✅ |
| 3_Sell 管理 | 已售商品删除被拦截（ValidationError）；未售商品可编辑（价格/标题生效）、可删除；他人在售商品编辑/删除返回 False（repo 层 `WHERE seller_id` 兜底） | ✅ |

### 3.2 用例 `test_marketplace_excludes_sold_and_foreign_rows`

- 商品广场只展示 available：成交后该商品从广场消失（total 1→0），但详情页仍可查（status=sold）——与 B 交接说明的「两条数据线」设计一致。✅

### 3.3 整合走查发现的行为顺序细节（记录，不修改）

`product_service.remove_product` 先查已售、后查所有权：非所有者删除**已售**商品会收到「已售出的商品不能删除（成交记录需保留）」的 `ValidationError`，而非通用的失败返回。两种路径都**不可删除**，保护语义完整，且该文案对演示更友好（明确告知原因）。按最小修改原则保持原实现，仅在此记录，并已体现在功能用例的断言中。

### 3.4 全套件汇总

```
python -m unittest discover -s tests -p "test_*.py"
Ran 13 tests in 0.66s — OK
```

| 套件 | 用例数 | 覆盖 |
| --- | :-: | --- |
| tests/transactions/test_purchase.py | 4 | Test 2.1–2.4 购买语义 |
| tests/transactions/test_concurrency.py | 2 | Test 2.5 多线程防超卖（10 轮） |
| tests/transactions/test_integrity.py | 5 | Test 2.6 完整性与约束强制力 |
| tests/functional/test_workflow_integration.py | 2 | Phase 3 端到端旅程 |

## 4. 静态整合检查

| 检查项 | 结果 |
| --- | --- |
| 三层边界：pages/services 中无 SQL、无 sqlite3 连接（grep 实证） | ✅ |
| SQL 只存在于 repositories/ | ✅ |
| pages 引用的 `ps.*` 接口在 services 中全部存在（AST 解析） | ✅ |
| 全工程 py_compile（app + 4 pages + services + repositories + database + check + A 的两脚本 + C 的测试） | ✅ |
| README「项目结构」树与实际文件一一对应（23 项全存在） | ✅ |
| requirements.txt 覆盖应用代码第三方依赖（streamlit；pandas/Faker 为数据脚本与预留） | ✅（备注见 §5.4） |
| orders 遗留物：无 order_repository.py / order_service.py / 第 5 页面；代码中「orders」仅存于说明性 docstring | ✅ |
| `.gitignore` 不忽略基准库（符合项目定位） | ✅ |

## 5. Streamlit 启动验证与环境事项

### 5.1 Streamlit 实机启动与页面验收 ✅（2026-11-21 完成）

经授权安装 `streamlit`（1.65.0，Python 3.10.0 环境）后，在**隔离验证副本**（`CampusMarket_Verify/`，独立数据库副本）上以
`python -m streamlit run app.py --server.headless=true` 启动，health 端点返回 `ok`，并用浏览器自动化完成全页面验收：

| 验收项 | 实测结果 |
| --- | --- |
| 首页渲染 | ✅ 指标 3,961/5/100 与审计实测一致；四页导航齐全 |
| 商品广场 | ✅ 共 3,961 件 · 第 1/199 页 · 每页 20 件；第 1 页「上一页」正确禁用 |
| 关键词搜索 | ✅ 「鼠标」命中 140 件、第 1/7 页（与 service 层实测一致），全部标题含关键词 |
| 发布商品 | ✅ 「发布成功，商品 #10001」，我的商品 15→16 件，状态 available |
| 自购拦截（UI） | ✅ 卖家 #1 购买自己的 #10001 → 「错误：不能购买自己发布的商品！」 |
| 购买闭环（UI） | ✅ 买家 #2 购买 #10001 → 自动跳转「我的购买」，成功提示 + 记录置顶（¥39.50，卖家 #1，成交时间 2026-11-21 16:12:05） |
| 已售状态（UI） | ✅ 详情页转 sold（买家 #2 + 成交时间），购买按钮结构性消失（重复购买被阻止） |
| 已售商品管理 | ✅ 卖家页 #10001 显示 sold，仅剩编辑表单 + 「已售出的商品保留成交记录，不能删除。」，删除按钮隐藏 |
| 副本行级核验 | ✅ #10001：buyer_id=2、status='sold'、finished_at='2026-11-21 16:12:05'；副本 sold 6039→6040 |
| 原始基准库 | ✅ 全程零写入，SHA-256 复核不变 |

界面截图（7 张）存档于 `presentation/screenshots/`，可直接用于视频与报告。

**环境备注：** 本机 pip 直连 PyPI/TUNA 均被网络中间盒以 `SSLEOFError` 掐断（curl/urllib 走 HTTP/1.1 正常）；改用阿里云镜像 HTTP 索引安装成功。录制环境如遇同样问题，可用
`pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com streamlit`。

### 5.2 数据口径事项

实库 available/sold = **3,961 / 6,039**，与文档口径 3,964/6,036 差 3 件（B 的 v3 购买验证遗留的 3 笔真实成交未回滚，溯源见 C_Project_Audit §6.1）。C 的报告一律采用实测值；对 A 的修改请求（§6.1 数据集口径）已单独列出，**未擅改任何文档或数据**。

### 5.3 测试遗留物与清理

`tests/transactions/.tmp/` 为临时副本目录（用例结束即清空）；`tests/transactions/results/concurrency_runs.json` 为并发测试真实数据存档，**有意保留**作为报告证据。

### 5.4 依赖备注（不修改）

`requirements.txt` 中 pandas 在应用代码中无 import、Faker 仅被留档脚本 `database/seed.py` 使用。二者保留原样：pandas 服务 A 的 §6 数据实验口径，Faker 与「勿重跑 seed.py」的警示一并留档。

## 6. C 阶段对工程的全部改动清单（完整记录）

**新增文件（零修改 A、B 既有代码）：**

```text
tests/__init__.py
tests/transactions/__init__.py
tests/transactions/testenv.py
tests/transactions/test_purchase.py
tests/transactions/test_concurrency.py
tests/transactions/test_integrity.py
tests/transactions/README.md
tests/transactions/results/concurrency_runs.json   （测试运行产物存档）
tests/functional/__init__.py
tests/functional/test_workflow_integration.py
docs/C_Project_Audit.md
docs/C_Transaction_Test_Report.md
docs/C_Integration_Report.md                       （本文件）
report/Section1–9 与 Final_Report.md               （Phase 4）
presentation/Video_Script.md / Demo_Checklist.md   （Phase 5）
```

**文档级增补（可逆、明确标注）：**

- `README.md` 末尾追加「C 的交付说明」章节（指向 tests/、docs/C_*.md、report/、presentation/）。

**未改动：** `database/`（含 campus_market.db，SHA-256 复核不变）、schema.sql、所有 repository/service/page 模块、check_interfaces.py、performance_test.py、test_repo.py、requirements.txt、B 的三份 docx。
