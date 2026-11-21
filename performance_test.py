import sqlite3
import time

DB_PATH = 'database/campus_market.db'

def test_query_performance(use_index=True):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    

    if use_index:

        query = "SELECT * FROM products WHERE category_id = 1 AND status = 'available'"
    else:

        query = "SELECT * FROM products WHERE category_id + 0 = 1 AND status = 'available'"
    

    start_time = time.time()
    cursor.execute(query)
    results = cursor.fetchall()

    end_time = time.time()
    
    conn.close()
    return (end_time - start_time) * 1000  

print("--- 🚀 数据库性能测试开始 ---")

print("⏳ 正在测试 [有索引] 查询...")
time_index = test_query_performance(use_index=True)
print(f"✅ 有索引耗时: {time_index:.2f} ms")

print("\n⏳ 正在测试 [无索引 - 全表扫描] 查询...")
time_no_index = test_query_performance(use_index=False)
print(f"🐢 无索引耗时: {time_no_index:.2f} ms")

print(f"\n🎉 性能对比结论：")
if time_index > 0:
    print(f"索引加速比高达: {time_no_index / time_index:.1f} 倍！")
else:
    print("数据量太小，耗时极短。")


print("\n--- 🔍 验证执行计划 (EXPLAIN QUERY PLAN) ---")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM products WHERE category_id = 1 AND status = 'available'")
plan = cursor.fetchall()
for row in plan:
    print(dict(row) if isinstance(row, sqlite3.Row) else row)
conn.close()