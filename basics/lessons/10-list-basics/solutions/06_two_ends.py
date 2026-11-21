n = int(input())
temps = []
for i in range(n):
    temps.append(int(input()))
k = int(input())
print(temps[k - 1], temps[-k])
