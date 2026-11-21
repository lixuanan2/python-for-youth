n = int(input())
jumps = []
for i in range(n):
    jumps.append(int(input()))
count = 0
for s in jumps:
    if s >= 60:
        count += 1
print(count)
