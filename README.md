# MKRWANProject
A sensor network of Arduino MKRWAN 1300s

MKRWAN.h is not my code, but the version here is modified by me.
This code works with the MKRWAN1300 Arduino Board.

Main documentation that is needed to complete this project is the LoraModem AT Commands. The MKRWAN.h library works above this level, and
it is hard to debug problems that arise with the low-level communication. Often times the modem misses ACKs from TTN, and times out
waiting for a response from the server.
