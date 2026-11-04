n = int(input())
steps = []
for i in range(n):
    steps.append(int(input()))
print("一共走了", sum(steps), "步")
print("走得最多的一天", max(steps), "步")
if 10000 in steps:
    print("有一天刚好一万步！")
