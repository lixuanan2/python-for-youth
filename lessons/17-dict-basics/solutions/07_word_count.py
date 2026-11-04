line = input()
counts = {}
for w in line.split():
    counts[w] = counts.get(w, 0) + 1
for w in counts:
    print(w, counts[w])
