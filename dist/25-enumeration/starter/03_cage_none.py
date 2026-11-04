heads = int(input())
feet = int(input())
for c in range(heads + 1):
    r = heads - c
    if c * 2 + r * 4 == feet:
        print("鸡", c, "兔", r)
# 一个答案也没有时，输出“没有答案”
# 提示：用一个变量记住“找到过没有”
