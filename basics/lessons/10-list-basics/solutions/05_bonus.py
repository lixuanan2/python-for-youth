n = int(input())
temps = []
for i in range(n):
    temps.append(int(input()))
k = int(input())
temps[k - 1] += 5
print(temps)
