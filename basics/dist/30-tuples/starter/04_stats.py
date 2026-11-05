def low_high(nums):
    return min(nums), max(nums)
n = int(input())
scores = []
for i in range(n):
    scores.append(int(input()))
low, high = low_high(scores)
print("最低", low, "最高", high)
print("相差", high - low)
