n = int(input())
jumps = []
for i in range(n):
    jumps.append(int(input()))
total = 0
for s in jumps:
    total += s
average = total / n
count = 0
for s in jumps:
    if s > average:
        count += 1
print(count)
