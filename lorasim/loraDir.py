#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
 LoRaSim 0.2.1: simulate collisions in LoRa
 Copyright © 2016 Thiemo Voigt <thiemo@sics.se> and Martin Bor <m.bor@lancaster.ac.uk>

 This work is licensed under the Creative Commons Attribution 4.0
 International License. To view a copy of this license,
 visit http://creativecommons.org/licenses/by/4.0/.

 Do LoRa Low-Power Wide-Area Networks Scale? Martin Bor, Utz Roedig, Thiemo Voigt
 and Juan Alonso, MSWiM '16, http://dx.doi.org/10.1145/2988287.2989163

 $Date: 2017-05-12 19:16:16 +0100 (Fri, 12 May 2017) $
 $Revision: 334 $
"""

"""
 SYNOPSIS:
   ./loraDir.py <nodes> <avgsend> <experiment> <simtime> [collision]
 DESCRIPTION:
    nodes
        number of nodes to simulate
    avgsend
        average sending interval in milliseconds
    experiment
        experiment is an integer that determines with what radio settings the
        simulation is run. All nodes are configured with a fixed transmit power
        and a single transmit frequency, unless stated otherwise.
        0   use the settings with the the slowest datarate (SF12, BW125, CR4/8).
        1   similair to experiment 0, but use a random choice of 3 transmit
            frequencies.
        2   use the settings with the fastest data rate (SF6, BW500, CR4/5).
        3   optimise the setting per node based on the distance to the gateway.
        4   use the settings as defined in LoRaWAN (SF12, BW125, CR4/5).
        5   similair to experiment 3, but also optimises the transmit power.
    simtime
        total running time in milliseconds
    collision
        set to 1 to enable the full collision check, 0 to use a simplified check.
        With the simplified check, two messages collide when they arrive at the
        same time, on the same frequency and spreading factor. The full collision
        check considers the 'capture effect', whereby a collision of one or the
 OUTPUT
    The result of every simulation run will be appended to a file named expX.dat,
    whereby X is the experiment number. The file contains a space separated table
    of values for nodes, collisions, transmissions and total energy spent. The
    data file can be easily plotted using e.g. gnuplot.
"""

import simpy
import random
import numpy as np
import math
import sys
import matplotlib.pyplot as plt
import os
from mpl_toolkits.mplot3d import Axes3D

# turn on/off graphics
graphics = 0

# do the full collision check
full_collision = False

# experiments:
# 0: packet with longest airtime, aloha-style experiment
# 1: one with 3 frequencies, 1 with 1 frequency
# 2: with shortest packets, still aloha-style
# 3: with shortest possible packets depending on distance



# this is an array with measured values for sensitivity
# see paper, Table 3
sf7 = np.array([7,-126.5,-124.25,-120.75])
sf8 = np.array([8,-127.25,-126.75,-124.0])
sf9 = np.array([9,-131.25,-128.25,-127.5])
sf10 = np.array([10,-132.75,-130.25,-128.75])
sf11 = np.array([11,-134.5,-132.75,-128.75])
sf12 = np.array([12,-133.25,-132.25,-132.25])

#store the locations of the nodes in a nice array so we can export to a .dat file
nodeList = []
packets = []

#
# check for collisions at base station
# Note: called before a packet (or rather node) is inserted into the list
def checkcollision(packet):
    col = 0 # flag needed since there might be several collisions for packet
    processing = 0
    for i in range(0,len(packetsAtBS)):
        if packetsAtBS[i].packet.processed == 1:
            processing = processing + 1
    if (processing > maxBSReceives):
        print ("too long")
        packet.processed = 0
    else:
        packet.processed = 1

    if packetsAtBS:
        print ("CHECK node {", packet.nodeid, "} (sf:{", packet.sf, "} bw:{",
               packet.bw, "} freq:{", packet.freq, "}) others: {", len(packetsAtBS), "}")
        for other in packetsAtBS:
            if other.nodeid != packet.nodeid:
               print (">> node {", other.packet.nodeid, "} (sf:{", other.packet.sf, "} bw:{",
               other.packet.bw, "} freq:{", other.packet.freq, "})")
               # simple collision
               if frequencyCollision(packet, other.packet) \
                   and sfCollision(packet, other.packet):
                   if full_collision:
                       if timingCollision(packet, other.packet):
                           # check who collides in the power domain
                           c = powerCollision(packet, other.packet)
                           # mark all the collided packets
                           # either this one, the other one, or both
                           for p in c:
                               p.collided = 1
                               if p == packet:
                                   col = 1
                       else:
                           # no timing collision, all fine
                           pass
                   else:
                       packet.collided = 1
                       other.packet.collided = 1  # other also got lost, if it wasn't lost already
                       col = 1
        return col
    return 0

#
# frequencyCollision, conditions
#
#        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
#        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
#        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
def frequencyCollision(p1,p2):
    if (abs(p1.freq-p2.freq)<=120 and (p1.bw==500 or p2.freq==500)):
        print ("frequency coll 500")
        return True
    elif (abs(p1.freq-p2.freq)<=60 and (p1.bw==250 or p2.freq==250)):
        print ("frequency coll 250")
        return True
    else:
        if (abs(p1.freq-p2.freq)<=30):
            print ("frequency coll 125")
            return True
        #else:
    print ("no frequency coll")
    return False

def sfCollision(p1, p2):
    if p1.sf == p2.sf:
        print ("collision sf node {", p1.nodeid, "} and node {", p2.nodeid, "}")
        # p2 may have been lost too, will be marked by other checks
        return True
    print ("no sf collision")
    return False

def powerCollision(p1, p2):
    powerThreshold = 6 # dB
    print ("pwr: node {", p1.nodeid, "} {", p1.rssi, "} dBm node {", p2.nodeid, "} {", p2.rssi, "} dBm; diff {", round(p1.rssi - p2.rssi,2), "} dBm")
    if abs(p1.rssi - p2.rssi) < powerThreshold:
        print ("collision pwr both node {", p1.nodeid, "} and node {", p2.nodeid, "}")
        # packets are too close to each other, both collide
        # return both packets as casualties
        return (p1, p2)
    elif p1.rssi - p2.rssi < powerThreshold:
        # p2 overpowered p1, return p1 as casualty
        print ("collision pwr node {", p2.nodeid, "} overpowered node {", p1.nodeid, "}")
        return (p1,)
    print ("p1 wins, p2 lost")
    # p2 was the weaker packet, return it as a casualty
    return (p2,)

def timingCollision(p1, p2):
    # assuming p1 is the freshly arrived packet and this is the last check
    # we've already determined that p1 is a weak packet, so the only
    # way we can win is by being late enough (only the first n - 5 preamble symbols overlap)

    # assuming 8 preamble symbols
    Npream = 8

    # we can lose at most (Npream - 5) * Tsym of our preamble
    Tpreamb = 2**p1.sf/(1.0*p1.bw) * (Npream - 5)

    # check whether p2 ends in p1's critical section
    p2_end = p2.addTime + p2.rectime
    p1_cs = env.now + Tpreamb
    print ("collision timing node {", p1.nodeid, "} ({", env.now - env.now, "},{", p1_cs - env.now,
           "},{", p1.rectime, "}) node {", p1.nodeid, "} ({", p2.addTime - env.now, "},{", p2_end - env.now, "})")
    if p1_cs < p2_end:
        # p1 collided with p2 and lost
        print ("not late enough")
        return True
    print ("saved by the preamble")
    return False

# this function computes the airtime of a packet
# according to LoraDesignGuide_STD.pdf
#
def airtime(sf,cr,pl,bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8   # number of preamble symbol (12.25  from Utz paper)

    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1

    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    print ("sf", sf, " cr", cr, "pl", pl, "bw", bw)
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream + Tpayload

#
# this function creates a node
#
class myNode():
    def __init__(self, nodeid, bs, period, packetlen):
        self.nodeid = nodeid
        self.period = period
        self.bs = bs
        self.x = 0
        self.y = 0
        self.z = 0

        # this is very complex prodecure for placing nodes
        # and ensure minimum distance between each pair of nodes
        found = 0
        rounds = 0
        global nodes
        while (found == 0 and rounds < 100):
            #create a random number that will be a seed to a location in the x and y direction
            a = random.random()
            b = random.random()
            c = random.random()
            if b<a:
                a,b = b,a #swaps values. same as temp=a, a=b, b=a in C/C++
            posx = b*maxDist*math.cos(2*math.pi*a/b)+bsx #create a X position based on the maxDistance variable from main.
            posy = b*maxDist*math.sin(2*math.pi*a/b)+bsy #create a Y position the same way.
            posz = b*maxDist*math.sin(2*math.pi*a/c)+bsz #MY UPDATE --> ADD A Z COORDINATE
            
            #Since we have added the z location, we are going to need to factor this into our distance calculation
            if len(nodes) > 0:
                for index, n in enumerate(nodes):
                    dist = np.sqrt(((abs(n.x-posx))**2)+((abs(n.y-posy))**2) + ((abs(n.z-posz))**2))#updated to calculate distance in 3 dimensions
                    if dist >= 10:
                        found = 1
                        self.x = posx
                        self.y = posy
                        self.z = posz
                    else:
                        rounds = rounds + 1
                        if rounds == 100:
                            print ("could not place new node, giving up")
                            exit(-1)
            else:
                print ("first node")
                self.x = posx
                self.y = posy
                self.z = posz
                found = 1
        self.dist = np.sqrt((self.x-bsx)*(self.x-bsx)+(self.y-bsy)*(self.y-bsy)+(self.z-bsz)*(self.z-bsz))
        nodeStr = "" + str(self.nodeid) + " " + str(self.x) + " " + str(self.y) + " " + str(self.z) + " " + str(self.dist) 
        print('node %d' %nodeid, "x", self.x, "y", self.y, "z", self.z, "dist: ", self.dist)
        nodeList.append(nodeStr)
        self.packet = myPacket(self.nodeid, packetlen, self.dist)
        self.sent = 0

        # graphics for node
        global graphics
        if (graphics == 1):
            global ax
            ax.add_artist(plt.Circle((self.x, self.y), 2, fill=True, color='blue'))

#
# this function creates a packet (associated with a node)
# it also sets all parameters, currently random
#
            
#we can extract info from these packets and match them up with the nodes they come from via the nodeid parameter
#this will be a nice way to get all of the rssi
class myPacket():
    def __init__(self, nodeid, plen, distance):
        #all of these global values are set in the main code at the bottom of this file labeled --> "MAIN PROGRAM"
        global experiment
        global Ptx
        global gamma
        global d0
        global var
        global Lpld0
        global GL

        self.nodeid = nodeid
        self.txpow = Ptx
        
        #this is the only section I have found so far that sets the signal parameters of the transmission packets
        #to do what we want we should edit these to accept values from our gui program
        #to implement this, we are gonna have to change the structure of the arguments passed to loraDir.py

        # randomize configuration values
        self.sf = random.randint(6,12)
        self.cr = random.randint(1,4)
        self.bw = random.choice([125, 250, 500])

        # for certain experiments override these
        if experiment==1 or experiment == 0:
            self.sf = 12
            self.cr = 4
            self.bw = 125

        # for certain experiments override these
        if experiment==2:
            self.sf = 6
            self.cr = 1
            self.bw = 500
        # lorawan
        if experiment == 4:
            self.sf = 12
            self.cr = 1
            self.bw = 125


        # for experiment 3 find the best setting
        # OBS, some hardcoded values
        Prx = self.txpow  ## zero path loss by default

        # log-shadow
        Lpl = Lpld0 + 10*gamma*math.log10(distance/d0)
        print ("Lpl:", Lpl)
        Prx = self.txpow - GL - Lpl #not sure what GL is, it is set to 0 in the main code. Lpl has something to do with sensitivity I beleive
        #Prx is the power of the signal recieved by the basestation --> the stuff being subtracted is likely assumed loss across the medium

        if (experiment == 3) or (experiment == 5):
            minairtime = 9999
            minsf = 0
            minbw = 0

            print ("Prx:", Prx)

            for i in range(0,6):
                for j in range(1,4):
                    if (sensi[i,j] < Prx):
                        self.sf = int(sensi[i,0])
                        if j==1:
                            self.bw = 125
                        elif j==2:
                            self.bw = 250
                        else:
                            self.bw=500
                        at = airtime(self.sf, 1, plen, self.bw)
                        if at < minairtime:
                            minairtime = at
                            minsf = self.sf
                            minbw = self.bw
                            minsensi = sensi[i, j]
            if (minairtime == 9999):
                print ("does not reach base station")
                exit(-1)
            print ("best sf:", minsf, " best bw: ", minbw, "best airtime:", minairtime)
            self.rectime = minairtime
            self.sf = minsf
            self.bw = minbw
            self.cr = 1

            if experiment == 5:
                # reduce the txpower if there's room left
                self.txpow = max(2, self.txpow - math.floor(Prx - minsensi))
                Prx = self.txpow - GL - Lpl
                print ("minsesi {", minsensi, "} best txpow {", self.txpow, "}")
        # transmission range, needs update XXX
        self.transRange = 150
        self.pl = plen
        self.symTime = (2.0**self.sf)/self.bw
        self.arriveTime = 0
        self.rssi = Prx #Prx
        #this is where we get the rssi into the file associated with the 
        # frequencies: lower bound + number of 61 Hz steps
        self.freq = 860000000 + random.randint(0,2622950)

        # for certain experiments override these and
        # choose some random frequences
        if experiment == 1:
            self.freq = random.choice([860000000, 864000000, 868000000])
        else:
            self.freq = 860000000

        print ("frequency" ,self.freq, "symTime ", self.symTime)
        print ("bw", self.bw, "sf", self.sf, "cr", self.cr, "rssi", self.rssi)
        self.rectime = airtime(self.sf,self.cr,self.pl,self.bw)
        print ("rectime node ", self.nodeid, "  ", self.rectime)
        # denote if packet is collided
        self.collided = 0
        self.processed = 0
        mystring = "" + str(self.nodeid) + " " + str(self.rssi) + " " + str(self.sf)#we can add to this to change the format so we can include more stats. Going to start with RSSI
        packets.append(mystring)

#
# main discrete event loop, runs for each node
# a global list of packet being processed at the gateway
# is maintained
#
def transmit(env,node):
    while True:
        yield env.timeout(random.expovariate(1.0/float(node.period)))

        # time sending and receiving
        # packet arrives -> add to base station

        node.sent = node.sent + 1
        if (node in packetsAtBS):
            print ("ERROR: packet already in")
        else:
            sensitivity = sensi[node.packet.sf - 7, [125,250,500].index(node.packet.bw) + 1]
            if node.packet.rssi < sensitivity:
                print ("node {", node.nodeid, "}: packet will be lost")
                node.packet.lost = True
            else:
                node.packet.lost = False
                # adding packet if no collision
                if (checkcollision(node.packet)==1):
                    node.packet.collided = 1
                else:
                    node.packet.collided = 0
                packetsAtBS.append(node)
                node.packet.addTime = env.now

        yield env.timeout(node.packet.rectime)

        if node.packet.lost:
            global nrLost
            nrLost += 1
        if node.packet.collided == 1:
            global nrCollisions
            nrCollisions = nrCollisions +1
        if node.packet.collided == 0 and not node.packet.lost:
            global nrReceived
            nrReceived = nrReceived + 1
        if node.packet.processed == 1:
            global nrProcessed
            nrProcessed = nrProcessed + 1

        # complete packet has been received by base station
        # can remove it
        if (node in packetsAtBS):
            packetsAtBS.remove(node)
            # reset the packet
        node.packet.collided = 0
        node.packet.processed = 0
        node.packet.lost = False

#
# "main" program
#

# get arguments
if len(sys.argv) >= 5:
    nrNodes = int(sys.argv[1])
    avgSendTime = int(sys.argv[2])
    experiment = int(sys.argv[3])
    simtime = int(sys.argv[4])
    if len(sys.argv) > 5:
        full_collision = bool(int(sys.argv[5]))
    print ("Nodes:", nrNodes)
    print ("AvgSendTime (exp. distributed):",avgSendTime)
    print ("Experiment: ", experiment)
    print ("Simtime: ", simtime)
    print ("Full Collision: ", full_collision)
else:
    print ("usage: ./loraDir <nodes> <avgsend> <experiment> <simtime> [collision]")
    print ("experiment 0 and 1 use 1 frequency only")
    exit(-1)


# global stuff --> change values here to change the simulation. All of the "global" values in myPacket and myNode are instantiated here
#Rnd = random.seed(12345)
nodes = []
packetsAtBS = []
env = simpy.Environment()

# maximum number of packets the BS can receive at the same time
maxBSReceives = 8


# max distance: 300m in city, 3000 m outside (5 km Utz experiment)
# also more unit-disc like according to Utz
bsId = 1
nrCollisions = 0
nrReceived = 0
nrProcessed = 0
nrLost = 0

Ptx = 14        #can set this to other values here --> global version that is used in the myPacket() function to set TX power of a packet
gamma = 2.08
d0 = 40.0         #I beleive this is the best possible RSSI, it is used to find Lpl from Lpld0 in myPacket()
var = 0           # variance ignored for now
Lpld0 = 127.41 #not sure what this is, cant find anything about Lpl in signal processing. It is used to calculate Prx in the myPacket() function
GL = 0         #also not sure what this is, also used ot calculate Prx in the myPacket() function

sensi = np.array([sf7,sf8,sf9,sf10,sf11,sf12])  #sensi is the sensitivity
if experiment in [0,1,4]:
    minsensi = sensi[5,2]  # 5th row is SF12, 2nd column is BW125
elif experiment == 2:
    minsensi = -112.0   # no experiments, so value from datasheet
elif experiment in [3,5]:
    minsensi = np.amin(sensi) ## Experiment 3 can use any setting, so take minimum --> minsensi is minimum sensitivity --> numpy.amin(*array) takes the minimum of a numpy array
Lpl = Ptx - minsensi
print ("amin", minsensi, "Lpl", Lpl)
maxDist = d0*(math.e**((Lpl-Lpld0)/(10.0*gamma)))
print ("maxDist:", maxDist)

# base station placement
bsx = maxDist+10
bsy = maxDist+10
bsz = maxDist+10
xmax = bsx + maxDist + 20
ymax = bsy + maxDist + 20
zmax = bsz + maxDist + 20
# prepare graphics and add sink
if (graphics == 1):
    plt.ion()
    plt.figure()
    ax = plt.gcf().gca()
    # XXX should be base station position
    ax.add_artist(plt.Circle((bsx, bsy), 3, fill=True, color='green'))
    ax.add_artist(plt.Circle((bsx, bsy), maxDist, fill=False, color='green'))


for i in range(0,nrNodes):
    # myNode takes period (in ms), base station id packetlen (in Bytes)
    # 1000000 = 16 min
    node = myNode(i,bsId, avgSendTime,20)
    nodes.append(node)
    env.process(transmit(env,node))

#prepare show
if (graphics == 1):
    plt.xlim([0, xmax])
    plt.ylim([0, ymax])
    plt.draw()
    plt.show()

# start simulation
env.run(until=simtime)

# print stats and save into file
print ("nrCollisions ", nrCollisions)

# compute energy
# Transmit consumption in mA from -2 to +17 dBm
TX = [22, 22, 22, 23,                                      # RFO/PA0: -2..1
      24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
      82, 85, 90,                                          # PA_BOOST/PA1: 15..17
      105, 115, 125]                                       # PA_BOOST/PA1+PA2: 18..20
# mA = 90    # current draw for TX = 17 dBm
V = 3.0     # voltage XXX
sent = sum(n.sent for n in nodes)
energy = sum(node.packet.rectime * TX[int(node.packet.txpow)+2] * V * node.sent for node in nodes) / 1e6

print ("energy (in J): ", energy)
print ("sent packets: ", sent)
print ("collisions: ", nrCollisions)
print ("received packets: ", nrReceived)
print ("processed packets: ", nrProcessed)
print ("lost packets: ", nrLost)

# data extraction rate
der = (sent-nrCollisions)/float(sent)
print ("DER:", der)
der = (nrReceived)/float(sent)
print ("DER method 2:", der)

# this can be done to keep graphics visible
if (graphics == 1):
    raw_input('Press Enter to continue ...')

# save experiment data into a dat file that can be read by e.g. gnuplot
# name of file would be:  exp0.dat for experiment 0
fname = "exp" + str(experiment) + ".dat"
print (fname)
if os.path.isfile(fname):
    res = "\n" + str(nrNodes) + " " + str(nrCollisions) + " "  + str(sent) + " " + str(energy)
else:
    res = "#nrNodes nrCollisions nrTransmissions OverallEnergy\n" + str(nrNodes) + " " + str(nrCollisions) + " "  + str(sent) + " " + str(energy)
with open(fname, "a") as myfile:
    myfile.write(res)
myfile.close()

#we want to plot the locations of the nodes relative to the base station at 0,0
#since they all have positive location values, we may get an odd looking graph
#to fix this, we can negate the location values of half the nodes, so it will be a more uniform
#circular distribution of nodes on the plot 

fname = "nodes" + str(experiment) + ".dat" #name would be loc0.dat for experiment 0
if not(os.path.isfile(fname)):
    res = "NodeID\t\tX\t\t\t\tY\t\t\t\tDistFromHub\t\t\t\tRSSI\t\t\t\tSF"
else:
    res = ""
with open(fname, "a") as myfile:
    myfile.write(res)
    for i in range(0, len(nodeList)):#range does the -1 for us! python is a little too easy sometimes
        line = packets[i].split()
        res = "\n" + nodeList[i] + " " + line[1] + " " + line[2]#appending the RSSI and SF from the packets array. can add more here when we add more to this string array
        myfile.write(res)
myfile.close()
print(fname)


#Graph Locations of the nodes relative to the basestation at (0,0)
#going to subtract 100 from each value so that the range is (-100, 100) for both x and y directions,
#currently range is (0,200) for both x and y
#to implement this, we need to get the contents of the file into into form and into 3 parrallel arrays
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
f.close()#to my understanding, the 'with' statement should close the file automatically when we leave it's scope,
# but I closed it manually to stay consistent with the author of the OP

#at this point in the program we have files and arrays filled with most of the information from the simultion.
#this begins the section of graphical programming, and traversing and associating speficific pieces of data from the arrays and files.
#IMPORTANT NOTE: As of 7/9, the arrays of the node information includes past experiments. If we want to only display data from the most recent experiment, the current
#best way to do this is to delete the nodesX.dat file from your lorasim folder. The program will create a new one with a header when it sees it does not exist during the sim.
#This means that we are seeing compounded graphs from each run of the program, showing all of the experiments data on one graph.

#NEXT TODO: Modify graph above so that the Spreading Factor of the node is displayed and the dots are color coded to show SF
#each of these will be just simple arrays of points but are now associated with Spreading Factors
sf6x=sf6y=[]
sf6y=[]
sf6z=[]
sf7x=[]
sf7y=[]
sf7z=[]
sf8x=[]
sf8y=[]
sf8z=[]
sf9x=[]
sf9y=[]
sf9z=[]
sf10x=[]
sf10y=[]
sf10z=[]
sf11x=[]
sf11y=[]
sf11z=[]
sf12x=[]
sf12y=[]
sf12z=[]

#now we have some good arrays that we can plot with our matplotlib as plt extension
plt.style.use('seaborn-whitegrid')
#plt.plot(bsx, bsy, 'o', color='r', label='basestation')#representation of the basestation
#this loop traversal is going to split our data into a few arrays so we can plot them all separately with different colors and labels
for i in range(0, len(sf)):
    if(sf[i] == 6):
        sf6x.append(x[i])
        sf6y.append(y[i])
        sf6z.append(z[i])
    if(sf[i] == 7):
        sf7x.append(x[i])
        sf7y.append(y[i])
        sf7z.append(z[i])
    if(sf[i] == 8):
        sf8x.append(x[i])
        sf8y.append(y[i])
        sf8z.append(z[i])
    if(sf[i] == 9):
        sf9x.append(x[i])
        sf9y.append(y[i])
        sf9z.append(z[i])
    if(sf[i] == 10):
        sf10x.append(x[i])
        sf10y.append(y[i])
        sf10z.append(z[i])
    if(sf[i] == 11):
        sf11x.append(x[i])
        sf11y.append(y[i])
        sf11z.append(z[i])
    if(sf[i] == 12):
        sf12x.append(x[i])
        sf12y.append(y[i])
        sf12z.append(z[i])
#at this point, we have the locations of nodes separated by what SF they are transmitting at      
"""plt.plot(sf6x, sf6y, 'o', color = 'b', label = 'SF6')
plt.plot(sf7x, sf7y, 'o', color = 'g', label = 'SF7')
plt.plot(sf8x, sf8y, 'o', color = 'c', label = 'SF8')
plt.plot(sf9x, sf9y, 'o', color = 'm', label = 'SF9')
plt.plot(sf10x, sf10y, 'o', color = 'y', label = 'SF10')
plt.plot(sf11x, sf11y, 'o', color = 'k', label = 'SF11')
plt.plot(sf12x, sf12y, 'o', color = 'purple', label = 'SF12')
"""
bsxList=[]
bsyList=[]
bszList=[]
bsxList.append(bsx)
bsyList.append(bsy)
bszList.append(bsz)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(bsxList, bsyList, bszList, 'o', color='r', label='basestation')
ax.plot(sf6x, sf6y, sf6z, 'o', color = 'b', label = 'SF6')
ax.plot(sf7x, sf7y, sf7z, 'o', color = 'g', label = 'SF7')
ax.plot(sf8x, sf8y, sf8z, 'o', color = 'c', label = 'SF8')
ax.plot(sf9x, sf9y, sf9z, 'o', color = 'm', label = 'SF9')
ax.plot(sf10x, sf10y, sf10z, 'o', color = 'y', label = 'SF10')
ax.plot(sf11x, sf11y, sf11z, 'o', color = 'k', label = 'SF11')
ax.plot(sf12x, sf12y, sf12z, 'o', color = 'purple', label = 'SF12')


#plt.plot(x, y, 'o', color='k', label='nodes')#all the nodes
plt.legend(loc='upper left')
plt.show()

  
print("done!")
# with open('nodes.txt','w') as nfile:
#     for n in nodes:
#         nfile.write("{} {} {}\n".format(n.x, n.y, n.nodeid))
# with open('basestation.txt', 'w') as bfile:
#     bfile.write("{} {} {}\n".format(bsx, bsy, 0))
