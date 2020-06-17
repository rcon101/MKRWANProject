# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 11:32:31 2020

@author: Ryanc
"""

from tkinter import *

def run():
    print("Run Program")

#initialize window frame
root = Tk()

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


#root.mainloop()
root.mainloop()
