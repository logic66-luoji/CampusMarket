from repositories.product_repository import search_products, get_product_detail

print("--- 测试 1：搜索商品 ---")
results = search_products(keyword="的", category_id=1)
print(f"共找到 {len(results)} 个商品。")
if len(results) > 0:
    print("第一个结果：", results[0])

print("\n--- 测试 2：查询商品详情 ---")
detail = get_product_detail(1)
if detail:
    print("商品详情：", detail['title'], "价格：", detail['price'])
else:
    print("没找到商品。")