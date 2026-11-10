# 【再加一档“良好”】
# 分数是 0 到 100 的整数，75 分到 89 分输出良好。
# 例如输入：75
# 应该输出：良好
# 提示：elif 可以写很多个，想想新的一档放在哪。
# ↓ 在下面这段程序上改

score = int(input())
if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
else:
    print("继续加油")
