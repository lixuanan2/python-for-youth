tries = 0
while True:
    password = input()
    tries += 1
    if password == "1234":
        print("开锁了！")
        break
    if tries == 3:
        print("错了 3 次，锁住了")
        break
    print("不对，再试试")
