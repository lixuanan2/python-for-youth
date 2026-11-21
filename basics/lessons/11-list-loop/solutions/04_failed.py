n = int(input())
jumps = []
for i in range(n):
    jumps.append(int(input()))
for s in jumps:
    if s < 60:
        print(s)
