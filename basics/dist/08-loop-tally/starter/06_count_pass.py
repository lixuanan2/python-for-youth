# 【几天读够了 20 页】
# 第一行读入天数 n，接下来 n 行，每行是这天读的页数。
#   输出有几天读了 20 页或更多。
# 例如输入（每个一行）：4、20、15、30、8
# 应该输出：2
# 提示：把累加换成计数，再加一个判断。
# ↓ 在下面这段程序上改

n = int(input())
total = 0
for i in range(n):
    pages = int(input())
    total += pages
print(total)
