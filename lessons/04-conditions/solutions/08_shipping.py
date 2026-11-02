w = int(input())
if w <= 1:
    cost = 10
else:
    cost = 10 + (w - 1) * 2
print("运费", cost, "元")
