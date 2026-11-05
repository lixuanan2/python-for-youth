try:
    age = int(input())
    print("明年你", age + 1, "岁")
except ValueError:
    print("请输入整数")
