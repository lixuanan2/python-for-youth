price = float(input())
count = int(input())
total = price * count
print(f"{count} 件，每件 {price:.2f} 元")
print(f"一共 {total:.2f} 元")
# 再加一行：打八折以后多少钱，也保留 2 位小数
