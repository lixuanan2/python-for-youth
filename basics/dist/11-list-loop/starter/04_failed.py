# 【把没达标的个数列出来】
# 第一行读入人数 n，接下来 n 行，每行一个整数，
#   是这人一分钟跳绳的个数。把不到 60 个的按原来的顺序输出，
#   一行一个；一个也没有就什么也不输出。
# 例如输入（每个一行）：4、80、59、60、30
# 应该输出（每个一行）：59、30
# 提示：不用数了，碰到就直接输出。
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
