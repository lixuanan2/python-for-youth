# 【再交回平均分】
# 在例题上改：函数改成一次交回三个值：最低、最高、平均分，
#   平均分用 round 保留 1 位小数。最后多输出一行“平均 多少”。
#   输入和例题一样，n 是 1 到 50 的整数。
# 例如输入（每个一行）：4、90、85、77、96
# 应该输出：
#   最低 77 最高 96
#   相差 19
#   平均 87.0
# 提示：让函数多交回一个。
# ↓ 在下面这段程序上改

def low_high(nums):
    return min(nums), max(nums)
n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
low, high = low_high(scores)
print("最低", low, "最高", high)
print("相差", high - low)
