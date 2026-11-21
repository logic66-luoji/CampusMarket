# CampusMarket 演示操作清单（Demo Checklist）

配套 `presentation/Video_Script.md`。本清单是录制当天的执行与核对表；
**每一步都必须在最终构建上可复现**。视频尚未录制（当前环境无 Streamlit），
本文件与讲稿即为可交付的录制准备物。

## 1. 录制前置条件（Pre-flight）

- [ ] 安装依赖：`pip install -r requirements.txt`（需要 streamlit≥1.31）
  - 本机 pip 直连 PyPI 被 TLS 中间盒掐断时的可用替代：
    `pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com streamlit`
    （2026-11-21 实测可装到 streamlit 1.65.0；pandas 已内置满足）
- [ ] 在工程根目录启动：`streamlit run app.py`，浏览器打开 http://localhost:8501
- [ ] 自检通过：`python check_interfaces.py` → 9/9 PASS
- [ ] 测试通过：`python -m unittest discover -s tests -p "test_*.py"` → 13 tests OK
- [ ] 基准库 SHA-256 复核：`d92adc77…37245fdd`（见 §5 校验命令）
- [ ] 屏幕分辨率 ≥ 1080p；浏览器 100% 缩放；隐藏书签栏与无关窗口
- [ ] 麦克风测试；录制软件（OBS / 系统录屏）就绪，全程英文讲解
- [ ] **不展示**任何密码或哈希；DB 浏览工具不打开 users.password_hash 列

## 2. 演示账号与商品（不改数据库，全部经应用界面准备）

| 角色 | 用法 | 说明 |
| --- | --- | --- |
| 卖家 | 侧边栏第一个测试账号（如 `#1 user_0_ndai`） | 负责发布/编辑演示商品 |
| 买家 | 侧边栏另一个测试账号 | 负责浏览/购买/查看历史 |
- [ ] 演示商品在录制中经「发布与管理」页真实发布（标题
  `DEMO Used Textbook - Calculus 7th Ed`，分类 书籍教材，价格 45 → 编辑为 39.5）
- [ ] 禁止直接 INSERT/UPDATE 数据库制造演示数据；禁止重跑 seed.py / patch_users.py
- [ ] 预演一次完整购买闭环后再正式录制（预演产生的成交记录留在库中属正常
  应用使用，但**不要**为表演而批量造数）

## 3. 分镜操作单（与讲稿逐段对应）

### Part 1 首页（0:40）
- [ ] 打开首页；念出项目定位；口头声明「登录为预设测试账号模拟」
- [ ] 指出三个指标卡：在售商品数、分类数、可切换账号数

### Part 2 架构（1:00）
- [ ] 切到 Figure 1 架构图（`report/figures/`）
- [ ] 回到工程树截图或编辑器：点出 pages → services → repositories → database 四层
- [ ] 打开 `database/connection.py` 展示 `PRAGMA foreign_keys = ON`（10 秒即可）

### Part 3 商品广场（1:00）
- [ ] 关键词搜索 `鼠标`（口译 "mouse"）→ 有结果
- [ ] 分类筛选 `电子产品`；价格区间 10–100；排序「价格从高到低」
- [ ] 点「下一页」展示分页与总数文案（共 N 件在售 · 第 X / Y 页）

### Part 4 卖家操作（1:00）
- [ ] 切到卖家账号 → 「发布与管理」
- [ ] 发布 DEMO 商品（标题/分类/价格/描述）
- [ ] 「我的商品」列表出现该商品（available）
- [ ] 编辑价格 45 → 39.5，保存后列表价格更新
- [ ] 指出已售商品无删除按钮（列表里若有已售商品，展开看提示文案）

### Part 5 购买闭环 ★（1:30）
- [ ] 侧边栏切到买家账号
- [ ] 商品广场搜 `DEMO` → 查看详情
- [ ] 详情页展示状态 available、卖家编号、购买区说明文案
- [ ] 点「购买此商品」→ 自动跳转「我的购买」
- [ ] 「我的购买」三个指标（已购件数/累计金额/最近成交）+ 新记录出现
- [ ] 回详情页再次尝试购买 → 红字「该商品已被别人抢先买走！」
- [ ] 切回卖家账号 → 我的作品列表该商品变 sold；详情页显示买家编号与成交时间
- [ ] （可选）买家再试自购：买家发布一件商品并尝试自购 →「不能购买自己发布的商品！」

### Part 6 数据库与测试（1:20）
- [ ] DB 浏览器/命令行展示三张表结构与两条索引
  （`PRAGMA table_info(products)`、`PRAGMA foreign_key_list(products)`）
- [ ] 终端运行 `python performance_test.py`（有索引 vs 全表扫描 + EXPLAIN QUERY PLAN）
- [ ] 终端运行 `python -m unittest discover -s tests -p "test_*.py" -v`
  （指出 concurrency 两项与 10 轮明细）
- [ ] 打开 `tests/transactions/results/concurrency_runs.json` 展示胜负明细
- [ ] 展示条件 UPDATE 语句（detail 页文案或代码 20 秒即可）

### Part 7 结论（0:30）
- [ ] 回首页；总结三句：完整交易闭环 / 条件更新保证一次性成交 / 13 项自动化测试

## 4. 录制后检查

- [ ] 全程英文、无口头禅卡顿；总时长 5–8 分钟
- [ ] 每个断言画面与讲稿一致（特别是失败提示文案）
- [ ] 画面无敏感信息（无密码/哈希/个人路径含姓名的特写需打码或避开）
- [ ] 导出 mp4（1080p，≥ 30fps），上传后填入
  `report/Section9_Deliverables.md` 的 Video URL 占位符
- [ ] GitHub 仓库建立/更新后填入 Section 9.1 的 Repository URL

## 5. 基准库完整性校验（录制前后各跑一次）

```bash
python - << 'EOF'
import hashlib
h = hashlib.sha256(open('database/campus_market.db','rb').read()).hexdigest()
print(h)
EOF
# 期望：d92adc770fed9df9e30d58944a7ecd7c18f3cc40a1fc244cf90f101337245fdd
# 说明：录制中的发布/购买是真实应用操作，会改变库内容（属正常业务数据）。
# 如需回到「纯基准快照」，用录制前备份的副本整体替换 database/campus_market.db；
# 除此之外不得手工改行、不得改 schema 或索引。
```

> 录制当日若时间紧张，最低保证 Parts 1、5、6 三段按本清单执行——它们分别
> 对应项目定位、核心事务语义、数据库与测试证据，是评分重点。
