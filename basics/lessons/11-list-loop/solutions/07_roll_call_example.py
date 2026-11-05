n = int(input())
names = []
for i in range(n):
    names.append(input())
for i in range(len(names)):
    print(i + 1, names[i], "到！")
print("一共", len(names), "人")
