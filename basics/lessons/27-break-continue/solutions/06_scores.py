total = 0
count = 0
while True:
    s = int(input())
    if s == -1:
        break
    if s < 0 or s > 100:
        continue
    total += s
    count += 1
if count == 0:
    print("没有有效分数")
else:
    print("有效", count, "个")
    print("平均", round(total / count, 1))
