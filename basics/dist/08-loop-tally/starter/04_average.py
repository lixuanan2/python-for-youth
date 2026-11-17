# 【改成输出平均分】
# 第一行读入人数 n，至少 1 人，接下来 n 行，每行一个整数分数。
# 例如输入（每个一行）：3、80、90、70
# 应该输出：80.0
# 提示：只要改最后一行。
# ↓ 在下面这段程序上改

n = int(input())
total = 0
for i in range(n):
    score = int(input())
    total += score
print(total)
