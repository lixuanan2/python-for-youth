def low_high(nums):
    return min(nums), max(nums)
n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
low, high = low_high(scores)
print("最低", low, "最高", high)
print("相差", high - low)
# 让函数再交回第三个值：平均分（用 round 保留 1 位小数）
# 最后多输出一行：平均 多少
