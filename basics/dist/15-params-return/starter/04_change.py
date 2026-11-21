# 【写一个找零函数】
# 起始程序里有 cost 函数。把它改成 change(paid, price)，
#   返回该找回多少钱（付的钱减去价钱）。分两行读入付了多少、
#   要付多少，都是整数，输出找零。
# 例如输入（每个一行）：20、14
# 应该输出：6
# 提示：换个名字，换个算法，别的不用动。
# ↓ 在下面这段程序上改

def cost(price, count):
    return price * count
price = int(input())
count = int(input())
print(cost(price, count))
