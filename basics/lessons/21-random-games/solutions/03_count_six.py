import random
random.seed(int(input()))
n = int(input())
count = 0
for i in range(n):
    if random.randint(1, 6) == 6:
        count += 1
print(count)
