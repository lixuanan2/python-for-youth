n = int(input())
dist = []
for i in range(n):
    dist.append(int(input()))
ranked = sorted(dist, reverse=True)
for i in range(len(ranked)):
    print(i + 1, ranked[i])
