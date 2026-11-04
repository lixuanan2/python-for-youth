n = int(input())
a = []
for k in range(n):
    a.append(int(input()))
target = int(input())
lo = 0
hi = n - 1
pos = -1
looks = 0
while lo <= hi and pos == -1:
    mid = (lo + hi) // 2
    looks += 1
    if a[mid] == target:
        pos = mid
    elif a[mid] < target:
        lo = mid + 1
    else:
        hi = mid - 1
print(pos)
print(looks)
