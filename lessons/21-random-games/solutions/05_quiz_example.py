import random
random.seed(int(input()))
a = random.randint(1, 10)
b = random.randint(1, 10)
answer = int(input())
if answer == a + b:
    print(a, "+", b, "=", a + b, "答对了！")
else:
    print(a, "+", b, "=", a + b, "再想想")
