n = int(input())
high = int(input())
low = high
for i in range(n - 1):
    t = int(input())
    if t > high:
        high = t
    if t < low:
        low = t
print(high - low)
