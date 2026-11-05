n = int(input())
table = []
for i in range(n):
    row = []
    for w in input().split():
        row.append(int(w))
    table.append(row)
for j in range(3):
    total = 0
    for i in range(n):
        total += table[i][j]
    print(total)
