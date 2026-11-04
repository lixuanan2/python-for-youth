words = ["pear", "apple", "kiwi", "banana"]
n = len(words)
for r in range(n - 1):
    for j in range(n - 1 - r):
        if words[j] > words[j + 1]:
            words[j], words[j + 1] = words[j + 1], words[j]
print(words)
