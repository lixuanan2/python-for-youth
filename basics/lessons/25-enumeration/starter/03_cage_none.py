heads = int(input())
feet = int(input())
for c in range(heads + 1):
    r = heads - c
    if c * 2 + r * 4 == feet:
        print("鸡", c, "兔", r)
