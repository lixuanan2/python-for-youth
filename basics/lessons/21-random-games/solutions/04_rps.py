import random
random.seed(int(input()))
me = input()
pc = random.choice(["石头", "剪刀", "布"])
print("电脑出", pc)
a = me == "石头" and pc == "剪刀"
b = me == "剪刀" and pc == "布"
c = me == "布" and pc == "石头"
if me == pc:
    print("平")
elif a or b or c:
    print("赢")
else:
    print("输")
