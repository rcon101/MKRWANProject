import os
import math
import simpy
import random
import numpy as np
import math
import sys
from tkinter import *
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk) 


def run():
    print("Run Program")
    #need to change this os.system line to extrace the data from the widgets
    collision="0"
    if menu_collision['text'] == "True":
        collision="1"
    params = [entry_numNodes.get(), entry_avgSend.get(), menu_experiment['text'],
              entry_simTime.get(), collision]
    cmdStr = "python loraDir.py " + params[0] + " " + params[1] + " " + params[2] + " " + params[3] + " " + params[4]
    
    print(cmdStr)
    os.system(cmdStr)

# plot function is created for 
# plotting the graph in 
# tkinter window 
def plot():
    
    #START NEW EDITS
    experiment = menu_experiment['text']#get the experiment number so we know what file to use
    fname = "nodes" + str(experiment) + ".dat"
    x = []#x locations
    y = []#y locations
    z = []#z locations
    dist = []#distance from the origin (hypotenuse)
    rssi = []#rssi for the associated node
    sf = []
    #we're going to implement this by opening the file becuase we want to use the contents of previous experiments as well
    #the gui will include a feature to delete this file
    first = 0
    with open(fname, "r") as f:
        for line in f:
            if(first==1):
                #format of nodesX.dat files is: <NodeID> <x> <y> <dist> <RSSI>
                l = line.split()#splits it into an array separated by the spaces
                #we can ignore the id so we only care about indices 1-3
                x.append(float(l[1]))
                y.append(float(l[2]))
                z.append(float(l[3]))
                dist.append(float(l[4]))
                rssi.append(float(l[5]))
                sf.append(float(l[6]))
            else:
                    first += 1
    f.close()
    #END NEW EDITS
    
    # the figure that will contain the plot 
    fig = Figure(figsize = (5, 5), 
				dpi = 100) 
    
    # list of squares 
    y = [i**2 for i in range(101)] 

	# adding the subplot 
    plot1 = fig.add_subplot(111) 

	# plotting the graph 
    plot1.plot(y) 

	# creating the Tkinter canvas 
	# containing the Matplotlib figure 
    canvas = FigureCanvasTkAgg(fig, 
							master = root) 
    canvas.draw()

	# placing the canvas on the Tkinter window 
    canvas.get_tk_widget().grid(columnspan=4)

	# creating the Matplotlib toolbar 
    toolbar = NavigationToolbar2Tk(canvas, 
								root) 
    toolbar.update() 

	# placing the toolbar on the Tkinter window 
    canvas.get_tk_widget().grid(columnspan=4)

# the main Tkinter window 
root = Tk() 

# setting the title 
root.title('LoraSim Plotting') 

# dimensions of the main window 
#root.geometry("500x500") 

#initialize all widgets

#title widgets
label_parameters = Label(root, text="Packet Parameters")
label_simulationParams = Label(root, text="Simulation Parameters")

#parameter label widgets
label_sf = Label(root, text="Spreading Factor", )
label_cr = Label(root, text="Coding Rate")
label_p = Label(root, text="TX Power")
label_cf = Label(root, text="Center Frequency")
label_bw = Label(root, text="Bandwidth")

#simulation parameter label widgets
label_numNodes = Label(root, text="Nodes")
label_avgSend = Label(root, text="Avg. Send(ms)")
label_experiment = Label(root, text="Experiment")
label_simtime = Label(root, text="Sim Time(ms)")
label_collision = Label(root, text="Collision Detection")

#text entry boxes for parameters
entry_sf = Entry(root)
entry_cr = Entry(root)
entry_p = Entry(root)
entry_cf = Entry(root)
entry_bw = Entry(root)

#initialize list and string var for dropdowns
v0 = StringVar(root)
expList = ["0", "1", "2", "3", "4", "5"]
v0.set(expList[0])
v1 = StringVar(root)
tfList = ["False", "True"]
v1.set(tfList[0])

#selection boxes for simulation parameters
entry_numNodes = Entry(root)
entry_avgSend = Entry(root)
menu_experiment = OptionMenu(root, v0, *expList)
entry_simTime = Entry(root)
menu_collision = OptionMenu(root, v1, *tfList)

#buttons
rightParams = [entry_numNodes, entry_avgSend, menu_experiment, entry_simTime, menu_collision]
runBtn = Button(root, text="Simulate", command=run)

#grid all widgets
#first column
label_parameters.grid(row=0, columnspan=2)
label_sf.grid(row=1, sticky=E)
label_cr.grid(row=2, sticky=E)
label_p.grid(row=3, sticky=E)
label_cf.grid(row=4, sticky=E)
label_bw.grid(row=5, sticky=E)

#second column
entry_sf.grid(row=1, column=1)
entry_cr.grid(row=2, column=1)
entry_p.grid(row=3, column=1)
entry_cf.grid(row=4, column=1)
entry_bw.grid(row=5, column=1)

#third column
label_simulationParams.grid(row=0, column=2, columnspan=2)
label_numNodes.grid(row=1, column=2, sticky=E)
label_avgSend.grid(row=2, column=2, sticky=E)
label_experiment.grid(row=3, column=2, sticky=E)
label_simtime.grid(row=4, column=2, sticky=E)
label_collision.grid(row=5, column=2, sticky=E)

#fourth column
entry_numNodes.grid(row=1, column=3)
entry_avgSend.grid(row=2, column=3)
menu_experiment.grid(row=3, column=3)
entry_simTime.grid(row=4, column=3)
menu_collision.grid(row=5, column=3)

#all columnms
runBtn.grid(columnspan=4)

# button that displays the plot 
plot_button = Button(master = root, 
					command = plot, 
					height = 2, 
					width = 10, 
					text = "Plot") 

# place the button
# in main window
plot_button.grid(columnspan=4)

# run the gui 
root.mainloop()

