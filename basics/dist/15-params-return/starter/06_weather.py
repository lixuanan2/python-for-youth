# 【写一个穿衣提示函数】
# 写 tip(t)：30 度及以上返回“很热”，15 度及以上返回“舒服”，
#   其余返回“冷”。读入一个整数气温，输出提示。
# 例如输入：32
# 应该输出：很热
# 提示：一个参数，三种结果，碰到 return 就结束。
# ↓ 在下面这段程序上改

def bigger(a, b):
    if a > b:
        return a
    return b
print(bigger(3, 8))
print(bigger(9, 2))
