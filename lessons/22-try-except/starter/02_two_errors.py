try:
    a = int(input())
    b = int(input())
    print(a // b)
except ValueError:
    print("要输入整数")
except ZeroDivisionError:
    print("除数不能是 0")
