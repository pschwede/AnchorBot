#!/bin/python
# https://en.wikipedia.org/wiki/Optimal_string_alignment
def levenshtein(s, t):
    m, n = len(s), len(t)
    d = [[0 for j in range(n)] for i in range(m)]

    for i in range(1, m):
        d[i][0] = i

    for j in range(1, n):
        d[0][j] = j

    for j in range(1, n):
        for i in range(1, m):
            if s[i] == t[j]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = min(d[i-1][j], d[i][j-1], d[i-1][j-1]) + 1
    return d[m-1][n-1]


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        print levenshtein(sys.argv[1], sys.argv[2])
    else:
        from timeit import Timer
        t = Timer("""
        n = 1
        for t in [str(hash(i)) for i in range(0,n)]:
            for s in [str(hash(i)) for i in range(2,n+2)]:
                print distance(s, t)
            ""","from levenshtein import distance").timeit()
