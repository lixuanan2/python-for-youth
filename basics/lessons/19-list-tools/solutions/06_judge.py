n = int(input())
s = []
for i in range(n):
    s.append(int(input()))
s = sorted(s)
middle = s[1:-1]
print(sum(middle) / len(middle))
