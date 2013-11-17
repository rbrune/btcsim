"""
bitcoin network simulator - btcsim
Copyright (C) 2013 Rafael Brune <mail@rbrune.de>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 and
only version 2 as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.
"""



import numpy

from heapq import *



class Event:
	def __init__(self, dest, orig, action, payload):
		self.dest = dest
		self.orig = orig
		self.action = action
		self.payload = payload

	def __lt__(self, other):
		return 0


class Block:
	def __init__(self, prev, height, time, miner_id, size, valid):
		self.prev = prev
		self.height = height
		self.time = time
		self.miner_id = miner_id
		self.size = size
		self.valid = valid

class Link:
	def __init__(self, dest, latency, bandwidth):
		self.dest = dest
		self.latency = latency
		self.bandwidth = bandwidth
		self.fulluntil = 0.0
	
	def occupy(self, t, t_size):
		base_t = t
		if self.fulluntil > base_t: base_t = self.fulluntil
		base_t += self.latency
		base_t += t_size/self.bandwidth
		self.fulluntil = base_t
		return base_t

class Miner:
	def __init__(self, miner_id, hashrate, verifyrate, seed_block, event_q, t):
		self.miner_id = miner_id
		self.hashrate = hashrate
		self.verifyrate = verifyrate
		self.verifyfulluntil = 0.0
		
		self.blocks = dict()
		self.chain_head = '*'
		
		self.blocks_new = []
		self.requested = dict()
		
		self.t = t
		self.event_q = event_q
		
		self.links = []
		
		self.add_block(seed_block)
		

	def mine_block(self):
		t_next = self.t + numpy.random.exponential(1/self.hashrate, 1)[0]
		t_size = 1024*200*numpy.random.random()
		t_block = Block(self.chain_head, self.blocks[self.chain_head].height + 1, t_next, self.miner_id, t_size, 1)
		self.send_event(t_next, self.miner_id, 'block', t_block)

	def verify_block(self, t_block):
		if (t_block.miner_id == self.miner_id) and (t_block.prev != self.chain_head):
			#print('%02d: block %s is to be ignored (old mining block event from before chain_head changed).' % (self.miner_id, hash(t_block)))
			return -1
		if t_block.valid != 1: 
			print('%02d: block %s is invalid.' % (self.miner_id, hash(t_block)))
			return -1
		if t_block.prev not in self.blocks: 
			#print('%02d: need previous block to verify block %s.' % (self.miner_id, hash(t_block)))
			return 0
		if t_block.height != self.blocks[t_block.prev].height + 1:
			print('%02d: height of block %s is invalid (%d / %d).' % (self.miner_id, hash(t_block), t_block.height, self.blocks[t_block.prev].height))
			return -1
		return 1

	def add_block(self, t_block):
		self.blocks[hash(t_block)] = t_block
		if (self.chain_head == '*'):
			self.chain_head = hash(t_block)
			self.mine_block()
			return
		if (t_block.height > self.blocks[self.chain_head].height):
			self.chain_head = hash(t_block)
			self.announce_block(self.chain_head)
			self.mine_block()

	def occupy(self, t, t_size):
		base_t = t
		if self.verifyfulluntil > base_t: base_t = self.verifyfulluntil
		base_t += t_size/self.verifyrate
		self.verifyfulluntil = base_t
		return base_t

	def process_new_blocks(self):
		rerun = 1
		while rerun == 1:
			rerun = 0
			blocks_later = []
			for t_block in self.blocks_new:
				validity = self.verify_block(t_block)
				if validity == 1: 
					#self.add_block(t_block)
					t = self.occupy(self.t, t_block.size)
					self.send_event(t, self.miner_id, 'addblock', t_block)
					#rerun = 1
				if validity == 0:
					blocks_later.append(t_block)
					self.request_block(-1, t_block.prev)
			self.blocks_new = blocks_later


	def receive_event(self, t, t_event):
		self.t = t
		if t_event.action == 'addblock':
			if t_event.orig != self.miner_id: print('received addblock not from myself!')
			self.add_block(t_event.payload)
			self.process_new_blocks()
		if t_event.action == 'block':
			self.blocks_new.append(t_event.payload)
			self.process_new_blocks()
		if t_event.action == 'newhead':
			if t_event.payload not in self.blocks:
				self.request_block(t_event.orig, t_event.payload)
		if t_event.action == 'getblock':
			if t_event.payload in self.blocks:
				self.send_block(t_event.orig, t_event.payload)

	def send_event(self, t, to, action, payload):
		t_event = Event(to, self.miner_id, action, payload)
		heappush(self.event_q, (t, t_event))

	def add_link(self, dest, latency, bandwidth):
		t_link = Link(dest, latency, bandwidth)
		self.links.append(t_link)

	def announce_block(self, t_hash):
		for t_link in self.links:
			t_arrival = t_link.occupy(self.t, 0)
			self.send_event(t_arrival, t_link.dest, 'newhead', t_hash)

	def request_block(self, to, t_hash):
		if t_hash in self.requested: return
		self.requested[t_hash] = 1
		for t_link in self.links:
			if (t_link.dest == to) or (to == -1):
				t_arrival = t_link.occupy(self.t, 0)
				self.send_event(t_arrival, t_link.dest, 'getblock', t_hash)

	def send_block(self, to, t_hash):
		for t_link in self.links:
			if t_link.dest == to:
				t_block = self.blocks[t_hash]
				t_arrival = t_link.occupy(self.t, t_block.size)
				self.send_event(t_arrival, t_link.dest, 'block', t_block)


