def total(n):
    if n == 1:
        return 1
    return n + total(n - 1)
print(total(int(input())))
# 改成阶乘：1 × 2 × … × n
# 函数名可以改成 fact
