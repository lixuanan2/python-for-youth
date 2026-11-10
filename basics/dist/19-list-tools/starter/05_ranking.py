# 【排一张名次表】
# 第一行读入人数 n（1 到 100 的整数），接下来 n 行，
#   每行一个 0 到 100 的整数分数。从高到低输出名次和分数，
#   一行一个，分数一样也各占一个名次。
# 例如输入（每个一行）：3、80、95、70
# 应该输出（每个一行）：1 95、2 80、3 70
# 提示：先从大到小排好，再用下标编名次。
# ↓ 在下面这段程序上改

n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
print("总分", sum(scores))
print("最高", max(scores))
print("最低", min(scores))
