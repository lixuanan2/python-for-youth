n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
total = 0
for s in scores:
    total += s
average = total / n
count = 0
for s in scores:
    if s > average:
        count += 1
print(count)
