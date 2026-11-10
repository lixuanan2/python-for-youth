# 【让程序说清楚】
# 分糖程序只输出两个数，别人看不懂。改成输出一句话。分两行读入：
#   糖是 0 到 1000 颗，人数是 1 到 100。
# 例如输入（每个一行）：7、2
# 应该输出：每人 3 颗，剩 1 颗
# 提示：print 里用逗号隔开，就能把文字和数字放在一起。
# ↓ 在下面这段程序上改

candy = int(input())
people = int(input())
print(candy // people)
print(candy % people)
