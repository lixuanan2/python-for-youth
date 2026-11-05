def sale(price, zhe):
    return price * zhe / 10
price = int(input())
print("打八折是", sale(price, 8), "元")
print("打五折是", sale(price, 5), "元")
