import os


def getVal(val):
    token = os.getenv(val)
    if token != "":
        return token

    token = open("/var/secrets/"+val.lower(), "r").read()
    return token
