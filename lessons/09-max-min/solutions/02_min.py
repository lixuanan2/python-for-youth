n = int(input())
low = int(input())
for i in range(n - 1):
    x = int(input())
    if x < low:
        low = x
print(low)
