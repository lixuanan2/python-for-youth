total = 0
count = 0
while True:
    m = int(input())
    if m == -1:
        break
    if m < 0 or m > 300:
        continue
    total += m
    count += 1
if count == 0:
    print("没有有效记录")
else:
    print("有效", count, "天")
    print("平均", round(total / count, 1))
