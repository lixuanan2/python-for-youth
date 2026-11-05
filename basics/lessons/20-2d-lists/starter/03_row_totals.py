n = int(input())
table = []
for i in range(n):
    row = []
    for w in input().split():
        row.append(int(w))
    table.append(row)
for i in range(n):
    print(i + 1, sum(table[i]))
