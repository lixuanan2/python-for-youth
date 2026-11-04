price = float(input())
count = int(input())
total = price * count
print(f"{count} 件，每件 {price:.2f} 元")
print(f"一共 {total:.2f} 元")
print(f"打八折 {total * 0.8:.2f} 元")
