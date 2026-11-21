# 说明：本文件是 A 同学早期版本的造数脚本，仅留档，请勿重跑。
# 当前 database/campus_market.db 由队友于 2026-11-19 重新生成：
# 1,000 用户 / 10,000 商品，含 buyer_id、finished_at 与在售、已售状态。
# 本脚本不产生这些字段，也不对应当前数据；报告 §6.1 请以实际 .db 为准。
import sqlite3
import random
from faker import Faker


fake = Faker('zh_CN')


conn = sqlite3.connect('campus_market.db')
cursor = conn.cursor()

# 1. 插入分类数据
categories = ['电子产品', '书籍教材', '生活用品', '服饰鞋包', '运动户外']
for cat in categories:
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
print("✅ 分类数据插入成功！")

# 2. 插入 100 个用户（卖家/买家）
print("正在生成 100 个用户...")
for _ in range(100):
    username = fake.user_name()
    password_hash = fake.sha256() 
    email = f"user_{_}_{fake.email()}" 
    cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)", 
                   (username, password_hash, email))


print("正在生成 10000 条商品数据，请稍候...")
for _ in range(10000):
    seller_id = random.randint(1, 100) # 假设 user_id 是 1-100
    category_id = random.randint(1, 5) # 假设 category_id 是 1-5
    title = fake.sentence(nb_words=4)[:-1] 
    description = fake.text(max_nb_chars=200)
    price = round(random.uniform(5.0, 5000.0), 2)
    
    cursor.execute(
        "INSERT INTO products (seller_id, category_id, title, description, price) VALUES (?, ?, ?, ?, ?)",
        (seller_id, category_id, title, description, price)
    )

# 提交事务并关闭连接
conn.commit()
conn.close()
print("🎉 10000 条数据生成完毕！")