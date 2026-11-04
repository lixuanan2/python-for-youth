a = [5, 2, 4, 1]
for j in range(3):
    if a[j] > a[j + 1]:
        a[j], a[j + 1] = a[j + 1], a[j]
    print(a)
