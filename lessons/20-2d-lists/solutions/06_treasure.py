n = int(input())
rows = []
for i in range(n):
    rows.append(input())
count = 0
for i in range(n):
    for j in range(len(rows[i])):
        if rows[i][j] == "#":
            print(i + 1, j + 1)
            count += 1
print(count)
