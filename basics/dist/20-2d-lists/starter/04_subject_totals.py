# 【每一科的总分】
# 输入和例题一样：第一行人数 n（1 到 30），接下来 n 行，
#   每行三个 0 到 100 的整数，用空格隔开。依次输出三科各自的总分，
#   一行一个。
# 例如输入（每个一行）：2、90 80 70、60 85 95
# 应该输出（每个一行）：150、165、165
# 提示：一行是一个人，一列是一科。这次要竖着加。
# ↓ 在下面这段程序上改

n = int(input())
table = []
for i in range(n):
    row = []
    for w in input().split():
        row.append(int(w))
    table.append(row)
for i in range(n):
    print(i + 1, sum(table[i]))
