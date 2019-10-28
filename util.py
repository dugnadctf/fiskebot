import os


def getVal(val):
    token = os.getenv(val)
    if token != "":
        return token

    token = open("/var/secrets/" + val.lower(), "r").read()
    return token


def trim_nl(s):
    import string

    ret = []
    consec_nl = 0
    for c in s:
        if c == "\n":
            consec_nl += 1
            if consec_nl == 2:
                ret.append("\n")
            elif consec_nl == 1:
                ret.append(" ")
            continue
        elif c in string.whitespace and consec_nl > 0:
            continue
        elif c != "\r":
            ret.append(c)
            consec_nl = 0
    return "".join(ret)
