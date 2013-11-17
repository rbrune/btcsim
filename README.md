Bitcoin Network Simulator
==============================================

--------------------------------------------------------------------------------
Copyright (C) 2013 Rafael Brune mail@rbrune.de


Purpose
-------

BTCsim is a stochastic event-based continous-time Bitcoin network simulator.
It can be used to study block chain generation and forking, block propagation,
network dynamics and miner/mining-pool interactions and strategies.


Project Status
--------------

At the moment it does not simulate propagation/inclusion of transactions but
it does simulate verification time and propagation time based on (random) block 
sizes, verification speed and network latency/bandwidth.

Included are two examples:
* attack-51.py demonstrates the effect of badly behaving miner with 51% of the network hashing power
* attack-selfish.py implements a selfish miner with 30% of the network hashing power

At the moment the implemented network messages are not a perfect mirror of the
Bitcoin protocol. For example the miners have to request missing blocks one-by-one
from connected nodes instead of receiving them all at once. This can lead to
slow-downs/lots of message passing with huge block-chain forks.

Contributors
------------

**Rafael Brune** mail@rbrune.de 1MNgscU4FbgSHw2LXSxuvAaqmZqfrJmdDG
