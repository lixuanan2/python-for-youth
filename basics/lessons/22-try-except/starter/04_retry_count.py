done = False
while not done:
    try:
        age = int(input())
        done = True
    except ValueError:
        print("不是整数，再输一次")
print("明年你", age + 1, "岁")
