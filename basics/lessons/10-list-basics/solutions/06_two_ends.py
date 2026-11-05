n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
k = int(input())
print(scores[k - 1], scores[-k])
