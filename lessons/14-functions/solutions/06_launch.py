def countdown():
    for i in range(3, 0, -1):
        print(i)
    print("发射！")
n = int(input())
for k in range(1, n + 1):
    print("第", k, "次")
    countdown()
