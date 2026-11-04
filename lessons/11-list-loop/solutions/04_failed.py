n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
for s in scores:
    if s < 60:
        print(s)
