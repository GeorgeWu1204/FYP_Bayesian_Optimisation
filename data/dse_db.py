import statistics
from pprint import PrettyPrinter
from colorama import Fore, Back, Style
import glob
import sys
import pickle
import os.path as osp

db_name='ppa_v2.db'
pp = PrettyPrinter(indent=4)
db = {}

#---------------------------------[generating database or loading it]----
if not osp.exists(db_name):
    print(f"[i] generating: '{db_name}'")
    if len(sys.argv) == 2:
        loc = sys.argv[1]
    else:
        loc = "**"

    for dbf in glob.glob(f'{loc}/ppa*.db', recursive=True):
        print(f"[i] loading db: '{dbf}'")

        with open(dbf, 'r') as f:
            local_db = eval(f.read())
            db.update(local_db)

    # pickle our database
    with open(db_name, 'wb') as f:
        pickle.dump(db, f)
else:
    print(f"[i] loading: '{db_name}'")
    with open(db_name, 'rb') as f:
        db.update(pickle.load(f))

#-------------------------------------------


# index: (arch, pre-type, btb)
#         arch: 1..12    (enum)
#         pre-type: 5..6 (enum)
#         btb: 4..255    (int)
# number of designs: 12*2*252=6048
print('number of designs: ', len(db))

# { ppa_metric: [ n0, n1, ... ] }
ppa_stats = { }
for point in db:
    ppa_db_point = db[point]
    print(f"{Fore.YELLOW}key: {point}{Style.RESET_ALL}")
    for k in ppa_db_point:

        if k not in ppa_stats: # initialize
            ppa_stats[k] = []

        val = ppa_db_point[k]
        if type(val) == tuple and len(val) == 2:
            val = val[0]
        if type(val) == bool:
            val = 1 if val else 0
        if type(val) not in [int, float]:
            raise RuntimeError(f"key '{k}' type '{type(val).__name__}' not supported!")
        ppa_stats[k].append(val)

# reduce
print("=====[statistics: (min, max, avg, stdev)]===")
for k in ppa_stats:
    val_lst = ppa_stats[k]
    ppa_stats[k] = tuple([min(val_lst), max(val_lst), round(statistics.fmean(val_lst), 2), round(statistics.pstdev(val_lst), 2) ])
    if ppa_stats[k][3] == 0:
       print(f"{Fore.RED}* {k} => {ppa_stats[k]}{Style.RESET_ALL}")
    else:
       print(f"{Fore.GREEN}* {k} => {ppa_stats[k]}{Style.RESET_ALL}")


