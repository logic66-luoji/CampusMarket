# CampusMarket

校园二手交易平台 · Track 1 / Database Application Development

本仓库包含可运行的 Streamlit 应用、SQLite 数据库与全部源码。
开发交接说明（已完成内容、后续待办、数据与接口约定）见 `docs/B_交接说明.docx`。

## 依赖（Dependencies）

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| Python | 3.13+（验证环境 3.13.14） | 运行时 |
| SQLite | Python 标准库内置，无需安装数据库服务 | 关系数据库 |
| streamlit | >= 1.31（验证环境 1.67.0） | Web 界面与多页面路由 |
| pandas | >= 2.0（验证环境 3.1.1） | 数据处理 |
| Faker | >= 30.0 | 历史造数脚本 `database/seed.py` 的依赖 |

完整依赖清单见 `requirements.txt`。

## 如何运行（How to run）

在工程根目录依次执行：

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 `http://localhost:8501`，终端按 `Ctrl+C` 停止服务。

- 数据库文件 `database/campus_market.db` 已随仓库提供，无需初始化或补账号
- 可选：`python check_interfaces.py` 执行只读联调自检
- 测试：`python -m unittest discover -s tests -p "test_*.py"` 执行全部 13 项自动化测试
- 当前数据：1,000 个用户、5 个分类、10,000 件商品（含在售与已售）

## 项目结构（Structure）

数据模型：`orders` 表已移除，成交状态记录在 `products.buyer_id`、
`products.finished_at` 与 `products.status`。

```
CampusMarket/
├── app.py                       主入口、当前账号、总览与页面导航
├── pages/
│   ├── 1_Marketplace.py         商品筛选、排序、分页与详情跳转
│   ├── 2_Product_Detail.py      商品详情与购买
│   ├── 3_Sell_MyProducts.py     发布、编辑、删除自己发布的商品
│   └── 4_My_Purchases.py        我的购买：成交记录与状态
├── services/                    业务层：参数校验与编排
│   ├── user_service.py
│   └── product_service.py
├── repositories/                数据访问层：SQL 集中于此
│   ├── product_repository.py    含 buy_product / get_my_purchases
│   ├── category_repository.py
│   └── user_repository.py
├── database/
│   ├── connection.py            统一连接工厂
│   ├── schema.sql               与 campus_market.db 一致的 DDL
│   ├── seed.py                  历史造数脚本（留档，勿重跑）
│   ├── patch_users.py           旧库补账号脚本（当前数据无需运行）
│   └── campus_market.db         数据文件（1,000 用户 / 10,000 商品）
├── docs/
│   ├── 注意事项.docx            A 同学早期交接说明（已过时）
│   ├── 修改说明_20261119.docx   队友 2026-11-19 更新说明
│   └── B_交接说明.docx          B 同学开发交接说明（v2）
├── tests/
│   ├── transactions/            购买事务语义与多线程防超卖（隔离副本运行）
│   └── functional/              service 层端到端用户旅程
├── report/                      最终报告与分节内容、设计图
├── presentation/                演示视频、字幕、讲稿与演示清单
├── performance_test.py          索引性能实验脚本
├── test_repo.py                 数据访问自测脚本
├── check_interfaces.py          联调自检脚本
├── requirements.txt
├── .gitignore
└── README.md
```
