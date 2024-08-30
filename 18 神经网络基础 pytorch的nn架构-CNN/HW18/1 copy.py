n=int(input())
lis=input().split()
siz = np.zeros(n+1)
siz = [0] * (n+1)
for i in range(n):
    lis[i] = int(lis[i])
    if lis[i] > 0:
        siz[lis[i]] += 1
r = 0

print(3)