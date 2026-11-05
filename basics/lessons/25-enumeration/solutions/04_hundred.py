n = int(input())
found = False
for cock in range(n // 5 + 1):
    for hen in range(n // 3 + 1):
        chick = n - cock - hen
        if chick >= 0 and chick % 3 == 0:
            if cock * 5 + hen * 3 + chick // 3 == n:
                print("公鸡", cock, "母鸡", hen, "小鸡", chick)
                found = True
if not found:
    print("没有答案")
