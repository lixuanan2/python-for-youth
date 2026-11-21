def tip(t):
    if t >= 30:
        return "很热"
    if t >= 15:
        return "舒服"
    return "冷"
t = int(input())
print(tip(t))
