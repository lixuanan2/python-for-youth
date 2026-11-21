n = int(input())
jumps = []
for i in range(n):
    jumps.append(int(input()))
for i in range(len(jumps)):
    jumps[i] += 5
print(jumps)
