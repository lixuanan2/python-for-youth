friends = [("小明", 3, 12), ("小红", 7, 1), ("小刚", 3, 30)]
month = int(input())
for name, m, d in friends:
    if m == month:
        print(f"{name} {m} 月 {d} 日过生日")
