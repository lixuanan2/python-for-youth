# 【每人补上 5 个】
# 第一行读入人数 n，接下来 n 行，每行一个整数跳绳个数。
#   计数器每人少记了 5 个，每人加 5，最后输出整个列表。
# 例如输入（每个一行）：3、80、95、70
# 应该输出：[85, 100, 75]
# 提示：换成用下标遍历，把加上的放回列表里。
# ↓ 在下面这段程序上改

n = int(input())
jumps = []
for i in range(n):
    jumps.append(int(input()))
count = 0
for s in jumps:
    if s >= 60:
        count += 1
print(count)
