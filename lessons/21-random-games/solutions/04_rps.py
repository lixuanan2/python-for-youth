import random
random.seed(int(input()))
me = input()
pc = random.choice(["石头", "剪刀", "布"])
print("电脑出", pc)
if me == pc:
    print("平")
elif (me == "石头" and pc == "剪刀") or (me == "剪刀" and pc == "布") or (me == "布" and pc == "石头"):
    print("赢")
else:
    print("输")
