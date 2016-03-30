import pickle
from datetime import datetime
import os
all_stats = []
stats = { '24h':[], '1h': [], '3d' : [], '1w' : []}
count = 0
print("parsing statistics_processed/")
for x in os.listdir('statistics_processed/'):
    tstamp = x.replace('players-', '')
    with open('statistics_processed/'+x, 'rb') as f:
        all_stats.append(pickle.load(f))
    count += 1

f = lambda x: x['timestamp']
stats = {'24h': sorted([e['24h'] for e in all_stats], key = f),
         '1h': sorted([e['1h'] for e in all_stats], key = f),
         '3d':sorted([e['3d'] for e in all_stats], key = f),
         '1w': sorted([e['1w'] for e in all_stats], key = f)
        }
#timestamp ofc
oldest = 1457709303
oldest_t = datetime.fromtimestamp(oldest)
# some filtering to avoid taking useless stats (1w activity at start is useless)
stats['24h'] = [e for e in stats['24h'] if oldest + 1*24*3600 < int(e['timestamp'])] 
stats['1w'] = [e for e in stats['1w'] if oldest + 7*24*3600 < int(e['timestamp'])] 
stats['3d'] = [e for e in stats['3d'] if oldest + 3*24*3600 < int(e['timestamp'])] 
print("done parsing !")
print("starting plot")
import matplotlib
matplotlib.use('agg')
import matplotlib.dates as md
import matplotlib.pyplot as plt
ax = plt.gca()
xfmt = md.DateFormatter('%m-%d')
ax.xaxis.set_major_formatter(xfmt)
for key, value in stats.items():
    x = [datetime.fromtimestamp(float(e["timestamp"])) for e in value]
    leagues = ["Perandus", "Standard", "Hardcore", "Hardcore Perandus"]
    for l in leagues:
        y = [e[l] for e in value]
        plt.cla()
        plt.clf()
        ax = plt.gca()
        xfmt = md.DateFormatter('%d-%m')
        ax.xaxis.set_major_formatter(xfmt)
        plt.plot(x, y, 'ro')
        plt.title("Activity in the last {} in {}".format(key, l))
        plt.show()
        plt.savefig("graphes/{}_{}.png".format(key,l))
           
print("Plot is done")
