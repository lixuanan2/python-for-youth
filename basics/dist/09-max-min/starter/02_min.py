# 【改成找最低分】
# 第一行读入人数 n（1 到 100 的整数），接下来 n 行，
#   每行一个 0 到 100 的整数分数。输出最低分。
# 例如输入（每个一行）：3、80、95、70
# 应该输出：70
# 提示：改一个符号，再给变量起个好懂的名字。
# ↓ 在下面这段程序上改

n = int(input())
best = int(input())
for i in range(n - 1):
    x = int(input())
    if x > best:
        best = x
print(best)
