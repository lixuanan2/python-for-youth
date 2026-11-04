n = int(input())
a = []
for k in range(n):
    a.append(int(input()))
for r in range(n - 1):
    for j in range(n - 1 - r):
        if a[j] > a[j + 1]:
            a[j], a[j + 1] = a[j + 1], a[j]
    print(a)
# 改成从大到小排
