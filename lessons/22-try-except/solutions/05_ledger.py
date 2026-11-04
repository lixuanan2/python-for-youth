n = int(input())
total = 0
bad = 0
for i in range(n):
    text = input()
    try:
        total = total + int(text)
    except ValueError:
        bad = bad + 1
print("和是", total)
print("不是整数的有", bad, "行")
