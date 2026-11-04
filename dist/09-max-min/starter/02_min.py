n = int(input())
best = int(input())
for i in range(n - 1):
    x = int(input())
    if x > best:
        best = x
print(best)
