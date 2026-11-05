done = False
while not done:
    try:
        price = float(input())
        done = True
    except ValueError:
        print("请输入数字，比如 10 或 2.5")
print("打五折后", price / 2, "元")
