n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
count = 0
for s in scores:
    if s >= 60:
        count += 1
print(count)
