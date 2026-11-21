n = int(input())
winner = input()
best = int(input())
for i in range(n - 1):
    name = input()
    price = int(input())
    if price > best:
        best = price
        winner = name
print(winner, best)
