# CampusMarket 录屏执行手册（目标成片 7 分钟，要求 5–8 分钟）

> 照本手册录完 → 把视频文件放到 `D:\作业\master 1\5003\project\录屏素材\`
> → 回复我一声 → 我负责：画面分段识别 → 英文字幕精确烧录 → 转码 → 推送仓库。
> **你不需要管字幕**——每幕的英文字幕我在后期按实际画面烧录。

---

## 一、录前准备（一次性，约 10 分钟）

### 1. 演示服务（我这边已常驻运行，确认即可）

- 应用：http://localhost:8501 （健康检查 ✅）
- 基准页：`http://127.0.0.1:8003/demo/backend_perf.html`、`backend_test.html`、
  `backend_schema.html`、`fig1.html`、`er.html`
- 演示库已是干净基准状态（1,000 用户 / 10,000 商品），你的发布/购买操作
  都落在这个隔离副本上，放心操作。**若重录第二次，先告诉我重置数据（1 分钟）**。

### 2. Edge 准备

1. `Ctrl+N` 开一个**新 Edge 窗口**（不要用有个人标签页的旧窗口）
2. 依次打开 6 个标签页（顺序＝演示顺序）：
   1. `http://localhost:8501`
   2. `http://127.0.0.1:8003/demo/backend_perf.html`
   3. `http://127.0.0.1:8003/demo/backend_test.html`
   4. `http://127.0.0.1:8003/demo/backend_schema.html`
   5. `http://127.0.0.1:8003/demo/fig1.html`
   6. `http://127.0.0.1:8003/demo/er.html`
3. 停在第 1 个标签页，`Ctrl+0` 重置缩放为 100%，最大化窗口

### 3. 录屏工具（二选一）

**方案一：Xbox Game Bar（Windows 自带，零安装，推荐）**
1. 聚焦 Edge 窗口，按 `Win+G` 打开；
2. 第一次使用需在设置里开启"游戏录制"（系统设置 → 游戏 → Xbox Game Bar）；
3. 点捕获面板的 ● 开始（或 `Win+Alt+R`），录制的是 **Edge 窗口**（自动干净，无桌面杂物）；
4. 停止：`Win+Alt+R`；文件在 `C:\Users\<你>\Videos\Captures\`。

**方案二：OBS Studio**
1. 来源添加「窗口采集」→ 选 Edge 窗口；
2. 设置 → 输出：1080p、码率 5000、编码 x264；
3. 开始/停止录制。

### 4. 开始录制前的最后检查

- [ ] Edge 已最大化、缩放 100%、只有上述 6 个标签页
- [ ] 停在第 1 个标签页（应用首页）
- [ ] 录屏已开始（Game Bar 录制角标出现）→ **静置 3 秒**再做第一幕

---

## 二、分幕执行表（16 幕 · 合计约 7 分钟）

> 通用规则：**每个动作做完停 2–3 秒**再进行下一个（给字幕和观看留时间）；
> 光标移动平缓；某幕做错 → 停 3 秒 → 重做该幕即可，后期我会剪掉失误段。
> 每幕的【英文字幕】由我后期烧录，**你不用管**——但你的操作节奏要和
> 幕序一致（我做画面分段识别）。

### 第 1 幕 · 约 15 秒 · 应用首页
- 停在首页不动；光标缓慢划过三个指标卡（3,961 / 5 / 100）和四页导航
- 【字幕】CampusMarket — a campus second-hand trading platform (Track 1 · Database Systems)

### 第 2 幕 · 约 35 秒 · 商品广场：关键词
- 点击侧边栏「商品广场」；关键词输入 `鼠标` → 回车 → **停 4 秒**看结果
  （应显示"共 140 件在售"）
- 【字幕】Keyword search — 140 available items match; the composite index seeks instead of scanning 10,000 rows

### 第 3 幕 · 约 50 秒 · 商品广场：价格/排序/分页
- 最低价 `10`、最高价 `800` → 停 3 秒；排序选「价格从高到低」→ 停 3 秒；
  点「下一页」→ 停 3 秒
- 【字幕】Price filter + whitelist sort + LIMIT/OFFSET pagination — all parameterized SQL in the repository layer

### 第 4 幕 · 约 60 秒 · 卖家：发布商品
- 切到侧边栏「发布与管理」；填表：标题 `DEMO Used Monitor`、价格 `39.5`、
  描述 `Used for one semester, original packaging, tested working` → 停 3 秒
  → 点「发布」→ **停 4 秒**看绿色成功提示（记下商品编号，后面要用）
- 【字幕】Publishing is validated by the service layer, then one INSERT with default status 'available'

### 第 5 幕 · 约 20 秒 · 卖家：已售保护
- 指向列表里任意一行带 `sold` 的商品（不展开），停顿展示
- 【字幕】Sold rows keep buyer & finished_at and cannot be deleted — completed sales are preserved

### 第 6 幕 · 约 15 秒 · 切换买家账号
- 侧边栏「当前测试账号」下拉选一个 `#2` 开头的账号 → 停 2 秒（页头变绿显示 #2）
- 【字幕】Switching to buyer account #2 — seller_id and buyer_id form two independent data lines

### 第 7 幕 · 约 40 秒 · 买家：搜索 + 详情
- 回「商品广场」；关键词输入 `Used Monitor` → 停 3 秒（应只有你的商品）
  → 点该卡片「查看详情」→ 停 4 秒
- 【字幕】The buyer searches for the demo listing and opens its detail page

### 第 8 幕 · 约 45 秒 · 购买（核心幕）
- 点「购买此商品」→ **停 5 秒**（自动跳转「我的购买」）→ 停 5 秒看成交记录
- 【字幕】Purchase = one conditional UPDATE … WHERE status='available' — exactly-once, decided by rowcount

### 第 9 幕 · 约 25 秒 · 我的购买
- 展示三个指标（已购件数/累计金额/最近成交）和新置顶记录
- 【字幕】Redirected to My Purchases — the new record tops the history

### 第 10 幕 · 约 25 秒 · 重复购买拦截
- 点该记录的「查看详情」回详情页 → **停 6 秒**展示：状态 sold、买家编号、
  成交时间、无购买按钮
- 【字幕】Revisiting the item: status 'sold' — a second purchase is rejected

### 第 11 幕 · 约 40 秒 · 查询执行基准（标签页 2）
- 切到 `backend_perf.html` 标签页，**缓慢滚动**看完 EXPLAIN 与两张基准表
- 【字幕】Query execution (real runs): EXPLAIN plans + benchmarks (8.2x → 12.8x covering-index traversal)

### 第 12 幕 · 约 35 秒 · 自动化测试（标签页 3）
- 切到 `backend_test.html`，展示 13 tests OK 与并发证据行
- 【字幕】13 automated tests: purchase semantics, 10 concurrent races, integrity, user journey

### 第 13 幕 · 约 25 秒 · 表结构（标签页 4）
- 切到 `backend_schema.html`，展示三表 DDL 与两个索引
- 【字幕】Database internals: three tables, two indexes, zero foreign-key violations

### 第 14 幕 · 约 20 秒 · 架构图（标签页 5）
- 切到 `fig1.html`
- 【字幕】Three-layer architecture: Streamlit → services → repositories → SQLite

### 第 15 幕 · 约 20 秒 · ER 图（标签页 6）
- 切到 `er.html`
- 【字幕】ER model: users publish & purchase products; categories group them

### 第 16 幕 · 约 15 秒 · 收尾
- 切回应用首页，停住结束
- 【字幕】Exactly-once purchases · layered design · verified by tests — thank you for watching

---

## 三、录完之后（我来做）

1. 视频文件放进 `D:\作业\master 1\5003\project\录屏素材\`（文件名任意），
   回复我"录好了"；
2. 我自动执行：**画面分段识别**（每幕切点）→ 按幕烧录英文字幕 → 转码
   1600×900 → 交付 `CampusMarket-demo.mp4` + `CampusMarket-demo.srt`；
3. 你上传 Google Drive（权限"任何有链接的人可查看"）→ 把链接给我 →
   我回填报告 §9.2、重导 PDF、推送仓库。

---

## 四、常见问题

| 问题 | 处理 |
| --- | --- |
| Game Bar 提示"此应用不支持录制" | 用 OBS 窗口采集替代；或改为「显示器采集」录全屏 |
| 录出来黑屏 | Edge 硬件加速冲突：Edge 设置 → 系统 → 关闭"使用硬件加速"后重启 Edge 再录 |
| 某一步手滑 | 停 3 秒重做该幕；后期我会剪掉 |
| 重录第二次发布同名商品 | 先告诉我重置演示数据，避免搜索出现两个同名商品 |
| 时长不够/超了 | 每幕停留时间弹性 ±50% 都没关系；字幕按实际画面分段烧录 |
