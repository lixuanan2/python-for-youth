wrong = 0
done = False
while not done:
    try:
        age = int(input())
        done = True
    except ValueError:
        print("不是整数，再输一次")
        wrong = wrong + 1
print("明年你", age + 1, "岁")
print("输错了", wrong, "次")
