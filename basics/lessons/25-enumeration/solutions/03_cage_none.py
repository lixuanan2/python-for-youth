heads = int(input())
feet = int(input())
found = False
for c in range(heads + 1):
    r = heads - c
    if c * 2 + r * 4 == feet:
        print("鸡", c, "兔", r)
        found = True
if not found:
    print("没有答案")
