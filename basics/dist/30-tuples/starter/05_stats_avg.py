# 【再交回平均】
# 在例题上改：函数改成一次交回三个值：最少、最多、平均，
#   平均用 round 保留 1 位小数。最后多输出一行“平均 多少”。
#   输入和例题一样，n 至少是 1。
# 例如输入（每个一行）：4、90、85、77、96
# 应该输出：
#   最少 77 最多 96
#   相差 19
#   平均 87.0
# 提示：让函数多交回一个。
# ↓ 在下面这段程序上改

def low_high(nums):
    return min(nums), max(nums)
n = int(input())
minutes = []
for i in range(n):
    minutes.append(int(input()))
low, high = low_high(minutes)
print("最少", low, "最多", high)
print("相差", high - low)
