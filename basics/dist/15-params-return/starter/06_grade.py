# 【写一个成绩等级函数】
# 写 grade(score)：90 分及以上返回“优秀”，60 分及以上返回“及格”，
#   其余返回“不及格”。读入一个 0 到 100 的整数分数，输出等级。
# 例如输入：95
# 应该输出：优秀
# 提示：一个参数，三种结果，碰到 return 就结束。
# ↓ 在下面这段程序上改

def bigger(a, b):
    if a > b:
        return a
    return b
print(bigger(3, 8))
print(bigger(9, 2))
