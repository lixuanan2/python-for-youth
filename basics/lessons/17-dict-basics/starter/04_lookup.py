price = {"苹果": 5, "香蕉": 3,
         "橙子": 4}
name = input()
if name in price:
    print(price[name])
else:
    print("没有这个商品")
