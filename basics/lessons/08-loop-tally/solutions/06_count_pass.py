n = int(input())
count = 0
for i in range(n):
    pages = int(input())
    if pages >= 20:
        count += 1
print(count)
