# 【全班每人加 5 分】
# 第一行读入人数 n（1 到 100 的整数），接下来 n 行，
#   每行一个 0 到 95 的整数分数。每人加 5 分，最后输出整个列表。
# 例如输入（每个一行）：3、80、95、70
# 应该输出：[85, 100, 75]
# 提示：换成用下标遍历，把加分放回列表里。
# ↓ 在下面这段程序上改

n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
count = 0
for s in scores:
    if s >= 60:
        count += 1
print(count)
