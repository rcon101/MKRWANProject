import matplotlib.pyplot as plt
#first thing we want to plot is a graph of SF vs airtime(ms) with three curves showing BW of 125kHz, 250kHz, and 500kHz

#need to fill these arrays in with data for avg airtime on each SF
bw125 = [30, 60, 250, 475, 900, 1800, 3300]
bw250 = [25, 50, 150, 280, 490, 800, 1500]
bw500 = [20, 40, 100, 200, 275, 450, 700]

sf = [6, 7, 8, 9, 10, 11, 12]

plt.plot(sf, bw125, label='BW 125kHz')
plt.plot(sf, bw250, label='BW 250kHz')
plt.plot(sf, bw500, label='BW 500kHz')
plt.ylabel('Packet Air Time [ms]')
plt.xlabel('Spreading Factor')
plt.legend(loc='upper left')
plt.grid(color='k', linestyle='-', linewidth=1)
plt.show()