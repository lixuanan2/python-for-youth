words = input().split()
print(len(words), "个词")
print(len(set(words)), "个不同的词")
print(" ".join(sorted(set(words))))
