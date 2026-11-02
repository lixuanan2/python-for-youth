secret = 7
guess = int(input())
while guess != secret:
    print("不对，再猜")
    guess = int(input())
print("猜对了")
