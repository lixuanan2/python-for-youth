done = False
while not done:
    try:
        age = int(input())
        done = True
    except ValueError:
        print("不是整数，再输一次")
print("明年你", age + 1, "岁")
# 再加一个计数：每输错一次加 1
# 最后输出“输错了 几 次”
