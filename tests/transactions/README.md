# tests/transactions — 事务与并发测试（Member C）

验证 CampusMarket 购买闭环的事务一致性与防超卖（anti-oversell）机制。
全部测试在**隔离数据库副本**上运行，真实基准库 `database/campus_market.db`
零写入（每轮结束自动复核 SHA-256）。

## 运行方式

在工程根目录（`CampusMarket_Final/`）执行：

```bash
python tests/transactions/test_purchase.py -v      # Test 2.1–2.4 顺序功能测试
python tests/transactions/test_concurrency.py -v   # Test 2.5 多线程并发竞争
python tests/transactions/test_integrity.py -v     # Test 2.6 数据完整性
# 或一次性：
python -m unittest tests.transactions.test_purchase tests.transactions.test_concurrency tests.transactions.test_integrity -v
```

只依赖 Python 标准库（`unittest` / `sqlite3` / `threading`），无 pytest 等新依赖。

## 文件说明

| 文件 | 内容 |
| --- | --- |
| `testenv.py` | 共用隔离环境：复制基准库到临时目录 → 逐模块替换 repository 实际引用的 `get_connection`（含 `product_repository` / `user_repository` / `category_repository`；直接只改 `database.connection` 无效，因为它们是名字绑定导入）→ tearDown 恢复原工厂、删除副本、复核基准库哈希 |
| `test_purchase.py` | Test 2.1 正常购买 / 2.2 重复购买 / 2.3 购买自己的商品 / 2.4 不存在的商品 |
| `test_concurrency.py` | Test 2.5：`threading.Barrier` 同步的双线程同时调用真实 `buy_product()`，10 轮竞争，每轮断言恰好一胜一负；明细写入 `results/concurrency_runs.json` |
| `test_integrity.py` | Test 2.6：基准库只读核查（10 条规则 + `PRAGMA foreign_key_check`）；副本上购买流程后复查；CHECK / 外键约束强制力（非法 status、负价格、无效引用必须 `IntegrityError`）；绕过业务层的半吊子篡改必须被规则捕获 |

## 隔离机制要点

1. 每个测试用例独立副本（`tests/transactions/.tmp/` 下，2 MB，跑完即删）。
2. 被测代码是**真实业务实现**：`buy_product` / `get_my_purchases` /
   `create_product` 等未改动一行，仅替换其连接工厂指向副本。
3. 测试数据经真实接口准备（`create_product` 发布在售商品），不直接 INSERT；
   只读断言用 SQL 直查副本。
4. 基准库哈希 `d92adc77…37245fdd` 在每个 tearDown 中强制复核，任何意外写入都会让测试失败。

## 预期结果摘要

- 顺序测试：正常购买成功且三字段正确；重复购买 / 自购 / 不存在商品全部失败且数据不变。
- 并发测试：每轮 2 线程竞争同一 available 商品，成功数=1、失败数=1，
  失败方提示「该商品已被别人抢先买走」，终态 `sold` + 胜者 buyer_id + 非 NULL 成交时间。
- 完整性测试：基准库 10 条规则 0 违规；约束注入全部被 `IntegrityError` 拒绝。

实测记录见 `docs/C_Transaction_Test_Report.md` 与 `results/concurrency_runs.json`。
