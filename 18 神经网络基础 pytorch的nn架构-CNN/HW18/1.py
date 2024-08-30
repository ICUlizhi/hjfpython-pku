n=int(input())
lis=input().split()

siz = [0] * (n+1)
for i in range(n):
    lis[i] = int(lis[i])
    if lis[i] > 0:
        siz[lis[i]] += 1
r = 0
for i in range(n+1):
    r += 2**siz[i] - 1

r = 2**(n-1) - 1 - r
print(int(r % (10**9 + 7)))