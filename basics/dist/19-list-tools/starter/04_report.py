n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
print("总分", sum(scores))
print("最高", max(scores))
print("最低", min(scores))
