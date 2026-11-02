secret = 7
guess = int(input())
while guess != secret:
    if guess > secret:
        print("大了")
    else:
        print("小了")
    guess = int(input())
print("猜对了")
