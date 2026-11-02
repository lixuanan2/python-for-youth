w = int(input())
if w <= 3:
    cost = 10
else:
    cost = 10 + (w - 3) * 2
print("运费", cost, "元")
