# 【改成找最便宜的】
# 第一行读入件数 n，至少 1 件，接下来 n 行，每行一个整数价格。
#   输出最低的价格。
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
