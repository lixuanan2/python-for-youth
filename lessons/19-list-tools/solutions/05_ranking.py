n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
ranked = sorted(scores, reverse=True)
for i in range(len(ranked)):
    print(i + 1, ranked[i])
