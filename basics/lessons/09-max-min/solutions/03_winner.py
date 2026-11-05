n = int(input())
winner = input()
best = int(input())
for i in range(n - 1):
    name = input()
    score = int(input())
    if score > best:
        best = score
        winner = name
print(winner, best)
