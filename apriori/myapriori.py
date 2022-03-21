import pandas as pd
import sys
from collections import OrderedDict
import numpy as np

def main():
    filename, minsup, minconf = sys.argv[1:]
    minsup, minconf = int(minsup), float(minconf)

    minsup_threshold = {30, 40, 50, 60, 70, 80, 90}
    minconf_threshold = {0.5, 0.6, 0.7}

    if minsup not in minsup_threshold or minconf not in minconf_threshold:
        if minsup not in minsup_threshold:
            print("Invalid minimum support")
            print("Valid values:\t{40, 50, 60, 70, 80}")
            print()
        if minconf not in minconf_threshold:
            print("Invalid minimum confidence")
            print("Valid values:\t{0.5, 0.6, 0.7}")
            print()
        return 

    fd = open(filename, mode='r',encoding='utf8',newline='\n')

    raw = fd.read().splitlines()

    hashtable = dict()

    for line in raw:
        first, second = line.split(sep="::")
        hashtable.setdefault(first, []).append(second)

    fd.close()
    
    # FP-Tree generateion of 4-itemsets with support count and pruning
    from collections import OrderedDict
    fp = OrderedDict()

    # 1-itemset support counting
    for t in hashtable.values():
        for ii in range(len(t)):
            i = int(t[ii])
            fp[i] = fp.get(i, OrderedDict())
            fp[i]["count"] = fp[i].get("count", 0) + 1

    # 2-itemset support counting
    for t in hashtable.values():
        for ii in range(len(t)):
            i = int(t[ii])
            # if support count is too low
            # prune 1-itemset
            if i in fp and fp[i]["count"] < minsup:
                continue
            if i not in fp:
                continue
            for ji in range(ii+1, len(t)):
                j = int(t[ji])
                fp[i][j] = fp[i].get(j, OrderedDict())
                fp[i][j]["count"] = fp[i][j].get("count", 0) + 1

    # 3-itemset support counting            
    for t in hashtable.values():
        for ii in range(len(t)):
            i = int(t[ii])
            # if fp[i]["count"] < minsup:
            #     continue
            if i not in fp:
                continue
            for ji in range(ii+1, len(t)):
                j = int(t[ji])
                # if support count is too low
                # prune 2-itemset
                if j in fp[i] and fp[i][j]["count"] < minsup:
                    del fp[i][j]
                    continue
                if j not in fp[i]:
                    continue    
                for ki in range(ji+1, len(t)):
                    k = int(t[ki])
                    fp[i][j][k] = fp[i][j].get(k, OrderedDict())
                    fp[i][j][k]["count"] = fp[i][j][k].get("count", 0) + 1

    # 4-itemset support couting
    for t in hashtable.values():
        for ii in range(len(t)):
            i = int(t[ii])
            # if fp[i]["count"] < minsup:
            #     continue
            if i not in fp:
                continue
            for ji in range(ii+1, len(t)):
                j = int(t[ji])
                # if fp[i][j]["count"] < minsup:
                #     continue
                if j not in fp[i]:
                    continue 
                for ki in range(ji+1, len(t)):
                    k = int(t[ki])
                    # if support count is too low
                    # prune 3-itemset
                    if k in fp[i][j] and fp[i][j][k]["count"] < minsup:
                        del fp[i][j][k]
                        continue
                    if k not in fp[i][j]:
                        continue
                    for li in range(ki+1, len(t)):
                        l = int(t[li])
                        fp[i][j][k][l] = fp[i][j][k].get(l, OrderedDict())
                        fp[i][j][k][l]["count"] = fp[i][j][k][l].get("count", 0) + 1
                    
    ctr = 0
    for k, v in fp.items():
        ctr += v["count"]
    fp["count"] = ctr

    # Support counting

    # Dictionary of 1-itemsets, 2-itemsets, 3-itemsets, and 4-itemsets with support count

    def generate(node, s, len=0):
        # Support count-based pruning
        if "count" in node and node["count"] < minsup:
            return
        if len >= 1:
            itemset = tuple(sorted(s))
            itemsets[len][itemset] = node["count"]
        if len == 4:
            return
        for k in node:
            if k != "count":
                generate(node[k], s + [int(k)], len+1)

    itemsets = dict()
    itemsets[1] = OrderedDict()
    itemsets[2] = OrderedDict()
    itemsets[3] = OrderedDict()
    itemsets[4] = OrderedDict()

    generate(fp, [])

    for k in itemsets:
        print(f"{k}-itemsets::{len(itemsets[k])}")

    # Frequency file generator with specified minsup
    freqfd = open(f"freq_{minsup}.txt", mode="w", encoding="utf8", newline="\n")

    for i in range(1, 5):
        for iset, ct in itemsets[i].items():
            tup = ", ".join(list(map(str, list(iset))))
            tup = "".join(["{", tup, "}"])
            freqfd.write(f"{tup}::{ct}\n")

    freqfd.close()

    # Rule generation for 2-itemsets with minsup a and minconf b
    rules = dict()
    rules[2] = dict()
    rules[3] = dict()
    rules[2]["antecedent"] = list()
    rules[2]["consequent"] = list()
    rules[2]["support count"] = list()
    rules[2]["confidence"] = list()
    rules[3]["antecedent"] = list()
    rules[3]["consequent"] = list()
    rules[3]["support count"] = list()
    rules[3]["confidence"] = list()


    for k, v in itemsets[2].items():
        f, s = k
        n, d = v, itemsets[1][tuple([f])]
        conf = n / d
        if conf >= minconf:
            rules[2]["antecedent"].append("".join(["{", str(f), "}"]))
            rules[2]["consequent"].append("".join(["{", str(s), "}"]))
            rules[2]["support count"].append(n)
            rules[2]["confidence"].append(round(conf, 4))
        d = itemsets[1][tuple([s])]
        conf = n / d
        if conf >= minconf:
            rules[2]["antecedent"].append("".join(["{", str(s), "}"]))
            rules[2]["consequent"].append("".join(["{", str(f), "}"]))
            rules[2]["support count"].append(n)
            rules[2]["confidence"].append(round(conf, 4))

    # Rule generation for 3-itemsets with minsup a and minconf b

    seen = set()

    def rule_gen_3_2(three: tuple, prevant: tuple):
        f, m, e = three
        pf, ps = prevant
        diff = list(set([f, m, e]).difference(set([pf, ps])))[0]
        ant, cons =  tuple([pf]), tuple(sorted([ps, diff]))
        n, d = itemsets[3][three], itemsets[1][ant]
        conf = n / d
        sant = ", ".join(list(map(str, list(ant))))
        sant = "".join(["{", sant, "}"])
        scons = ", ".join(list(map(str, list(cons))))
        scons = "".join(["{", scons, "}"])
        rulestr = f"{sant}\t--->\t{scons}"
        if conf >= minconf and rulestr not in seen:
            seen.add(rulestr)
            rules[3]["antecedent"].append(sant)
            rules[3]["consequent"].append(scons)
            rules[3]["support count"].append(n)
            rules[3]["confidence"].append(round(conf, 4))
            # rules[3][rulestr] = [round(conf, 4), n]
        ant, cons =  tuple([ps]), tuple(sorted([pf, diff]))
        n, d = itemsets[3][three], itemsets[1][ant]
        conf = n / d
        sant = ", ".join(list(map(str, list(ant))))
        sant = "".join(["{", sant, "}"])
        scons = ", ".join(list(map(str, list(cons))))
        scons = "".join(["{", scons, "}"])
        rulestr = f"{sant}\t--->\t{scons}"
        if conf >= minconf and rulestr not in seen:
            seen.add(rulestr)
            rules[3]["antecedent"].append(sant)
            rules[3]["consequent"].append(scons)
            rules[3]["support count"].append(n)
            rules[3]["confidence"].append(round(conf, 4))
            # rules[3][rulestr] = [round(conf, 4), n]
        

    def rule_gen_3(three: tuple):
        f, m, e = three
        ant = tuple(sorted([m, e]))
        cons  = tuple([f])
        n, d = itemsets[3][three], itemsets[2][ant]
        conf = n / d
        sant = ", ".join(list(map(str, list(ant))))
        sant = "".join(["{", sant, "}"])
        scons = ", ".join(list(map(str, list(cons))))
        scons = "".join(["{", scons, "}"])
        rulestr = f"{sant}\t--->\t{scons}"
        if conf >= minconf and rulestr not in seen:
            rules[3]["antecedent"].append(sant)
            rules[3]["consequent"].append(scons)
            rules[3]["support count"].append(n)
            rules[3]["confidence"].append(round(conf, 4))
            # rules[3][f"{sant}\t--->\t{scons}"] = [round(conf, 4), n]
            rule_gen_3_2(three, ant)
        ant, cons = tuple(sorted([f, e])), tuple([m])
        n, d = itemsets[3][three], itemsets[2][ant]
        conf = n / d
        sant = ", ".join(list(map(str, list(ant))))
        sant = "".join(["{", sant, "}"])
        scons = ", ".join(list(map(str, list(cons))))
        scons = "".join(["{", scons, "}"])
        rulestr = f"{sant}\t--->\t{scons}"
        if conf >= minconf and rulestr not in seen:
            rules[3]["antecedent"].append(sant)
            rules[3]["consequent"].append(scons)
            rules[3]["support count"].append(n)
            rules[3]["confidence"].append(round(conf, 4))
            # rules[3][f"{sant}\t--->\t{scons}"] = [round(conf, 4), n]
            rule_gen_3_2(three, ant)
        ant, cons = tuple(sorted([f, m])), tuple([e])
        n, d = itemsets[3][three], itemsets[2][ant]
        sant = ", ".join(list(map(str, list(ant))))
        sant = "".join(["{", sant, "}"])
        scons = ", ".join(list(map(str, list(cons))))
        scons = "".join(["{", scons, "}"])
        rulestr = f"{sant}\t--->\t{scons}"
        conf = n / d
        if conf >= minconf and rulestr not in seen:
            rules[3]["antecedent"].append(sant)
            rules[3]["consequent"].append(scons)
            rules[3]["support count"].append(n)
            rules[3]["confidence"].append(round(conf, 4))
            # rules[3][f"{sant}\t--->\t{scons}"] = [round(conf, 4), n]
            rule_gen_3_2(three, ant)
    
    
    for k, v in itemsets[3].items(): 
        rule_gen_3(k)

    #Dataframe for 2-itemset rules

    two_itemset_rules = pd.DataFrame(rules[2])

    three_itemset_rules = pd.DataFrame(rules[3])

    itemset_rules = pd.concat([two_itemset_rules, three_itemset_rules])

    rulesfn = f"rules_{minsup}_{minconf}.txt"

    rfdw = open(rulesfn, mode='w',encoding='utf8', newline="")

    np.savetxt(rulesfn, itemset_rules, delimiter="::", fmt="%s")

    rfdw.close()

    return

if __name__=="__main__":
    main()