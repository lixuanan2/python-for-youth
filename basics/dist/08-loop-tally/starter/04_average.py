# 【平均每天读几页】
# 第一行读入天数 n，至少 1 天，接下来 n 行，每行是这天读的页数。
#   输出平均每天读几页。
# 例如输入（每个一行）：3、20、30、10
# 应该输出：20.0
# 提示：只要改最后一行。
# ↓ 在下面这段程序上改

n = int(input())
total = 0
for i in range(n):
    pages = int(input())
    total += pages
print(total)
