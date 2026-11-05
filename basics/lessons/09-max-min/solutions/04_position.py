n = int(input())
best = int(input())
place = 1
for k in range(2, n + 1):
    x = int(input())
    if x > best:
        best = x
        place = k
print(place, best)
