n = int(input())
best = int(input())
for i in range(n - 1):
    jumps = int(input())
    if jumps > best:
        best = jumps
print("跳得最多的一次是", best, "下")
