n = int(input())
dist = []
for i in range(n):
    dist.append(int(input()))
print("一共", sum(dist))
print("最远", max(dist))
print("最近", min(dist))
