def low_high(nums):
    return min(nums), max(nums)
n = int(input())
minutes = []
for i in range(n):
    minutes.append(int(input()))
low, high = low_high(minutes)
print("最少", low, "最多", high)
print("相差", high - low)
