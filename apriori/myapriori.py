import pandas as pd
import sys
from collections import OrderedDict

def main():
    filename, minsup, minconf = sys.argv[1:]
    minsup, minconf = int(minsup), float(minconf)
    fd = open(filename, mode='r',encoding='utf8',newline='\n')

    raw = fd.read().splitlines()

    hashtable = dict()

    for line in raw:
        first, second = line.split(sep="::")
        hashtable.setdefault(first, []).append(second)
    
    return

if __name__=="__main__":
    main()