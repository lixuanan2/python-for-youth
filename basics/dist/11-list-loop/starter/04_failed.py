# 【把不及格的分数列出来】
# 第一行读入人数 n（1 到 100 的整数），接下来 n 行，
#   每行一个 0 到 100 的整数分数。
#   把不到 60 分的分数按原来的顺序输出，一行一个；
#   一个也没有就什么也不输出。
# 例如输入（每个一行）：4、80、59、60、30
# 应该输出（每个一行）：59、30
# 提示：不用数了，碰到就直接输出。
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
