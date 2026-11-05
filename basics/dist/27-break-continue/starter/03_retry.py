while True:
    try:
        age = int(input())
        break
    except ValueError:
        print("不是整数，再输一次")
print("明年你", age + 1, "岁")
