import sys


def read_lines(path):
    # open in rb mode so \r stays and bad utf-8 doesnt crash
    with open(path, "rb") as f:
        lines = f.read().split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    return lines


#myers linear space version 
# search from the start and from the end together until both meet.
#the meeting point is on a shortest path so we can split there.
# returns (x, y) counted from a0, b0
def middle_snake(a, a0, a1, b, b0, b1):
    n = a1 - a0
    m = b1 - b0
    max_d = (n + m + 1) // 2
    off = max_d + 1  #add this to k so k can be negative
    size = 2 * max_d + 3
    vf = [-1] * size  # V array going forward
    vb = [-1] * size  # V array going backward (x from the end)
    vf[off + 1] = 0
    vb[off + 1] = 0
    delta = n - m
    odd = delta % 2 == 1
    #to skip diagonals that went out of the grid
    fstart = fend = bstart = bend = 0

    # i = k + off is the index in V
    #diagonal k going forward = diagonal delta - k going backward
    cross = 2 * off + delta

    for d in range(max_d + 1):
        lo = off - d  # k = -d
        hi = off + d  # k = d

        #forward search
        for i in range(lo + fstart, hi + 1 - fend, 2):
            if i == lo or (i != hi and vf[i - 1] < vf[i + 1]):
                x = vf[i + 1]  # down
            else:
                x = vf[i - 1] + 1  #right
            y = x - i + off
            if x < n and y < m and a[a0 + x] == b[b0 + y]:
                x += 1
                y += 1
                #check 32 at once first, its faster than one by one
                while x + 32 <= n and y + 32 <= m and a[a0 + x:a0 + x + 32] == b[b0 + y:b0 + y + 32]:
                    x += 32
                    y += 32
                while x < n and y < m and a[a0 + x] == b[b0 + y]:
                    x += 1
                    y += 1
            vf[i] = x
            if x > n:
                fend += 2
            elif y > m:
                fstart += 2
            elif odd:
                c = cross - i
                if 0 <= c < size and vb[c] != -1 and x >= n - vb[c]:
                    return x, y

        #backward search, same as above but from the end
        for i in range(lo + bstart, hi + 1 - bend, 2):
            if i == lo or (i != hi and vb[i - 1] < vb[i + 1]):
                x = vb[i + 1]
            else:
                x = vb[i - 1] + 1
            y = x - i + off
            if x < n and y < m and a[a1 - 1 - x] == b[b1 - 1 - y]:
                x += 1
                y += 1
                while x + 32 <= n and y + 32 <= m and a[a1 - x - 32:a1 - x] == b[b1 - y - 32:b1 - y]:
                    x += 32
                    y += 32
                while x < n and y < m and a[a1 - 1 - x] == b[b1 - 1 - y]:
                    x += 1
                    y += 1
            vb[i] = x
            if x > n:
                bend += 2
            elif y > m:
                bstart += 2
            elif not odd:
                c = cross - i
                if 0 <= c < size and vf[c] != -1:
                    fx = vf[c]
                    if fx >= n - x:
                        return fx, fx - (c - off)
    return None


#used for lines and also for characters in highlight
#keep_a[i] = 1 if a[i] is kept, 0 if deleted (same for b)
def diff(a, b):
    # a line that is only in one file can never be kept, so remove those first. answer stays same but myers runs much faster
    in_a = set(a)
    in_b = set(b)
    pos_a = [i for i in range(len(a)) if a[i] in in_b]
    pos_b = [j for j in range(len(b)) if b[j] in in_a]
    small_a = [a[i] for i in pos_a]
    small_b = [b[j] for j in pos_b]
    ka, kb = myers(small_a, small_b)

    keep_a = bytearray(len(a))
    keep_b = bytearray(len(b))
    for t in range(len(pos_a)):
        if ka[t]:
            keep_a[pos_a[t]] = 1
    for t in range(len(pos_b)):
        if kb[t]:
            keep_b[pos_b[t]] = 1
    return keep_a, keep_b


def myers(a, b):
    keep_a = bytearray(len(a))
    keep_b = bytearray(len(b))
    todo = [(0, len(a), 0, len(b))]
    while todo:
        a0, a1, b0, b1 = todo.pop()
        # keep matching lines at start and end
        while a0 < a1 and b0 < b1 and a[a0] == b[b0]:
            keep_a[a0] = 1
            keep_b[b0] = 1
            a0 += 1
            b0 += 1
        while a0 < a1 and b0 < b1 and a[a1 - 1] == b[b1 - 1]:
            a1 -= 1
            b1 -= 1
            keep_a[a1] = 1
            keep_b[b1] = 1
        if a0 == a1 or b0 == b1:
            continue
        mid = middle_snake(a, a0, a1, b, b0, b1)
        if mid is None:
            continue
        x, y = mid
        todo.append((a0, a0 + x, b0, b0 + y))
        todo.append((a0 + x, a1, b0 + y, b1))
    return keep_a, keep_b


def ranges(keep):
    parts = []
    i = 0
    while i < len(keep):
        if keep[i]:
            i += 1
            continue
        start = i
        while i < len(keep) and not keep[i]:
            i += 1
        parts.append(str(start) + "-" + str(i))
    if not parts:
        return "."
    return ",".join(parts)


def highlight_line(old, new):
    # decode so one emoji = one character
    old = old.decode("utf-8", "surrogateescape")
    new = new.decode("utf-8", "surrogateescape")
    keep_old, keep_new = diff(old, new)
    return ("? " + ranges(keep_old) + " | " + ranges(keep_new) + "\n").encode()


def make_output(a, b, highlight):
    keep_a, keep_b = diff(a, b)

    out = []
    i = 0
    j = 0
    while i < len(a) or j < len(b):
        # print all - lines first then + lines
        del_start = i
        while i < len(a) and not keep_a[i]:
            i += 1
        ins_start = j
        while j < len(b) and not keep_b[j]:
            j += 1
        for t in range(del_start, i):
            out.append(b"-" + a[t] + b"\n")
        for t in range(ins_start, j):
            out.append(b"+" + b[t] + b"\n")
            old = del_start + (t - ins_start)  #1st - goes with 1st +
            if highlight and old < i:
                out.append(highlight_line(a[old], b[t]))
        if i < len(a) and j < len(b):
            out.append(b" " + a[i] + b"\n")
            i += 1
            j += 1
    return b"".join(out)


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2
    command, a_path, b_path = sys.argv[1:]
    try:
        a = read_lines(a_path)
        b = read_lines(b_path)
    except OSError as e:
        print("cannot read file:", e, file=sys.stderr)
        return 2
    sys.stdout.buffer.write(make_output(a, b, command == "highlight"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
