n = int(input())
count = 0
for i in range(n):
    score = int(input())
    if score >= 60:
        count += 1
print(count)
