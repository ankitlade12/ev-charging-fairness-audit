from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/evfair-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams.update({"pdf.fonttype":42,"ps.fonttype":42})
fig,ax=plt.subplots(figsize=(3.5,1.7));ax.set(xlim=(0,10),ylim=(0,5));ax.axis('off')
boxes=[(.1,2.2,2.5,1.35,'Evaluator\nFuture event log'),(3.7,2.2,2.4,1.35,'Current\nobservations'),(7.3,2.2,2.5,1.35,'Controller\nForecast + plan'),(3.7,.1,2.4,1.25,'Applied power\nEnergy ledger'),(7.3,.1,2.5,1.25,'Completed-only\nservice history')]
for x,y,w,h,label in boxes:
 ax.add_patch(Rectangle((x,y),w,h,facecolor='#f2f2f2',edgecolor='#555555',lw=.7));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=7)
for a,b in [((2.6,2.85),(3.7,2.85)),((6.1,2.85),(7.3,2.85)),((8.5,2.2),(5.4,1.35)),((3.7,.75),(1.3,2.2)),((8.5,1.35),(8.5,2.2))]:
 ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','lw':.8})
ax.text(5,4.45,'Observe → decide → verify → apply',ha='center',fontsize=8)
fig.tight_layout(pad=.15);fig.savefig('figures/information.pdf')
