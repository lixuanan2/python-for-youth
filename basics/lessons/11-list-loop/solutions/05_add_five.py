n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
for i in range(len(scores)):
    scores[i] += 5
print(scores)
