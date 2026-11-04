def bigger(a, b):
    if a > b:
        return a
    return b
a = int(input())
b = int(input())
c = int(input())
print(bigger(bigger(a, b), c))
