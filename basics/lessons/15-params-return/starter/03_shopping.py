def cost(price, count):
    return price * count
p1 = int(input())
c1 = int(input())
p2 = int(input())
c2 = int(input())
s1 = cost(p1, c1)
s2 = cost(p2, c2)
print(s1 + s2)
