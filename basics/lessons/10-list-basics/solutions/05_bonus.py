n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
k = int(input())
scores[k - 1] += 5
print(scores)
