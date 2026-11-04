seconds = int(input())
h = seconds // 3600
m = seconds % 3600 // 60
s = seconds % 60
print(f"{h:02d}:{m:02d}:{s:02d}")
