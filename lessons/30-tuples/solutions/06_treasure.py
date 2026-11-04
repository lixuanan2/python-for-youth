n = int(input())
points = []
for i in range(n):
    x, y = input().split()
    points.append((int(x), int(y)))
best = points[0]
for p in points:
    if abs(p[0]) + abs(p[1]) < abs(best[0]) + abs(best[1]):
        best = p
print(best)
print(abs(best[0]) + abs(best[1]), "步")
