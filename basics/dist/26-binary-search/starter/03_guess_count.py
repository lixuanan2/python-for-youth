# 【最后说出猜了几次】
# 在例题上改：每猜一次，计数加 1。猜中以后，
#   再输出一行“猜了 几 次”。秘密数是 1 到 100 的整数。
# 例如输入：42
# 应该输出（每个一行）：50、25、37、43、40、41、42、猜了 7 次
# 提示：加一个计数器。
# ↓ 在下面这段程序上改

secret = int(input())
lo = 1
hi = 100
guess = 0
while guess != secret:
    guess = (lo + hi) // 2
    print(guess)
    if guess < secret:
        lo = guess + 1
    elif guess > secret:
        hi = guess - 1
