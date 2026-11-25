def low_high_avg(nums):
    return min(nums), max(nums), round(sum(nums) / len(nums), 1)
n = int(input())
minutes = []
for i in range(n):
    minutes.append(int(input()))
low, high, avg = low_high_avg(minutes)
print("最少", low, "最多", high)
print("相差", high - low)
print("平均", avg)
