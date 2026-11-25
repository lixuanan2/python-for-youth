# 【每样东西一共卖了几件】
# 输入和例题一样：第一行天数 n，接下来 n 行，每行三个整数，
#   用空格隔开。依次输出三样东西各自的总数，一行一个。
# 例如输入（每个一行）：2、90 80 70、60 85 95
# 应该输出（每个一行）：150、165、165
# 提示：一行是一天，一列是一样东西。这次要竖着加。
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
