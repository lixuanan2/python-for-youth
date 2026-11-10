# 【从 1 乘到 n】
# 读入 n（1 到 10 的整数），输出 1 × 2 × 3 × … × n。
#   这个数叫 n 的阶乘。在例题上改，想一想出口还是 1 吗。
# 例如输入：4
# 应该输出：24
# 提示：把加法换成乘法。
# ↓ 在下面这段程序上改

def total(n):
    if n == 1:
        return 1
    return n + total(n - 1)
print(total(int(input())))
