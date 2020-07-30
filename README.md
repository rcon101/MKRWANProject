# MKRWANProject
A sensor network of Arduino MKRWAN 1300s

MKRWAN.h is not my code, but the version here is modified by me.
This code works with the MKRWAN1300 Arduino Board.

Main documentation that is needed to complete this project is the LoraModem AT Commands. The MKRWAN.h library works above this level, and
it is hard to debug problems that arise with the low-level communication. Often times the modem misses ACKs from TTN, and times out
waiting for a response from the server.

The python scripts are all written in Python 2, besides LoraDir.py, which I've updated to Python 3. The rest require updates to the print statements to work. This could include simply commenting them out, but this won't yield any useful information.


6/24/2020 12:30pm Commit --> Updates to gui2.py and loraDir.py
-added functionality in loraDir.py to extract location information of nodes and store in a file name locX.dat, X being the experiment(0-5) being used
-added feature that plots the nodes relative to the basestation located at (0,0) in loraDir.py


7/9/2020 2:30pm Commit --> Uploaded new versions of gui2.py and loraDir.py
-added feature in loraDir that when run, graphs all node locations relative to basestation and color codes them by SF
-gui2.py was uploaded to ensure compatability

7/30/2020
Updated LoraDir.py
-now runs the same simulation in a 3d space
-adds functionality to randomize the nodes in a 3rd dimension
