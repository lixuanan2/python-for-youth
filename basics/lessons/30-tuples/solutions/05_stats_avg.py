def low_high_avg(nums):
    return min(nums), max(nums), round(sum(nums) / len(nums), 1)
n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
low, high, avg = low_high_avg(scores)
print("最低", low, "最高", high)
print("相差", high - low)
print("平均", avg)
