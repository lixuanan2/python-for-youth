money = int(input())
times = 0
total = 0
while money != 0:
    times += 1
    total += money
    money = int(input())
print("存了", times, "次，一共", total, "元")
