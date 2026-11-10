# 【把不同的词列出来】
# 在例题上改：最后再输出一行，把不同的词从小到大排好，
#   用一个空格连起来。输入一行英文，词和词之间用空格隔开。
# 例如输入：i like cats i like dogs
# 应该输出：
#   6 个词
#   4 个不同的词
#   cats dogs i like
# 提示：再加一行输出。
# ↓ 在下面这段程序上改

words = input().split()
print(len(words), "个词")
print(len(set(words)), "个不同的词")
