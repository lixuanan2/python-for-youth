# 【掷 n 次，有几个 6】
# 第一行读入种子，第二行读入次数 n（0 到 1000 的整数）。
#   用这个种子掷 n 次骰子，输出一共掷出了几次 6。
# 例如输入（每个一行）：1、10
# 应该输出：1
# 提示：不猜了，用循环掷很多次，数一数。
# ↓ 在下面这段程序上改

import random
random.seed(int(input()))
secret = random.randint(1, 100)
guess = int(input())
while guess != secret:
    if guess > secret:
        print("大了")
    else:
        print("小了")
    guess = int(input())
print("猜中了！")
