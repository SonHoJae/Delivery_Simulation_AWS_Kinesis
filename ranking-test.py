from collections import OrderedDict
ranking = [{'a':5},{'c':2},{'d':1}]
print(ranking)

def insertToRank(data):
    global ranking
    for idx, dat in enumerate(reversed(ranking)):
        key = [k for k in dat.keys()][0]
        data_key = [k for k in data.keys()][0]
        if dat[key] >= data[data_key]:
            # print(dat)
            # print(idx)
            # print(data)
            ranking = ranking[0:len(ranking)-idx] + [data] + ranking[len(ranking)-idx:]
            print(ranking)
            break
    return ranking

insertToRank({'b':3})
insertToRank({'b':4})
insertToRank({'b':3})


# def insertToRank(data):
#     global ranking
#     for idx, dat in enumerate(reversed(ranking)):
#         if dat >= data:
#             # print(dat)
#             # print(idx)
#             # print(data)
#             print(ranking[0:len(ranking)-idx])
#             ranking = ranking[0:len(ranking)-idx] + [data] + ranking[len(ranking)-idx:]
#             print(ranking)
#             break
#     return ranking