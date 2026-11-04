for x in range(100, 1000):
    a = x // 100
    b = x // 10 % 10
    c = x % 10
    if a + b + c == 10 and a == c:
        print(x)
