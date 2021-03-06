from twisted.internet import reactor, protocol
import Messages
import urllib
import logging as Logger
from bitstring import BitArray
import time
import struct
import Constants
import time
from Constants import *
import math

class RequestManager():
	def __init__(self, torrent):
		self.torrent 						= torrent
		self.peers_requesting_blocks		= dict()			#Initialize dictionary storing peers requesting each block
		self.divide_blocks_number			= DIVISION_BLOCK_NUMBER
		self.initial_request_number 		= INITIAL_REQUEST_NUMBER
		self.total_requests					= 0
		self.total_requests_sent			= 0
		self.total_requests_cancelled		= 0
		self.total_requests_wasted			= 0
		self.total_requests_used			= 0
		self.total_data_received			= 0
		self.peerlist_of_pieces				= [dict() for x in range(self.torrent.file_manager.no_of_pieces)]
		# self.initListOfPeersRequestingBlocks()

	# def initListOfPeersRequestingBlocks(self):
	# 	self.list_of_peers_requesting_blocks = list()
	# 	for piece_index in range(self.torrent.file_manager.no_of_pieces):
	# 		self.list_of_peers_requesting_blocks.append(list())
	# 		for block_offset in range(self.torrent.file_manager.getBlockCountFor(piece_index)):
	# 			self.list_of_peers_requesting_blocks[piece_index].append(list())

	def get_next_block(self, peer):
		if(self.total_requests == MAX_TOTAL_REQUESTS):
			return -1,-1
		piece_id 				= self.torrent.file_manager.current_pos_piece_id
		block_offset 			= self.torrent.file_manager.current_block_offset
		block_number 			= 0
		requests_allowed		= self.initial_request_number
		while(1):
			if(piece_id in self.peers_requesting_blocks):
				if(block_offset not in self.peers_requesting_blocks[piece_id]):
					self.peers_requesting_blocks[piece_id][block_offset] = dict()
			else:
				self.peers_requesting_blocks[piece_id] = dict()
				self.peers_requesting_blocks[piece_id][block_offset] = dict()
			if(self.canRequestBlock(piece_id,block_offset,requests_allowed,peer)):
				return piece_id,block_offset
			block_number += 1
			if(block_number == self.divide_blocks_number and requests_allowed>1):
				block_number = 0
				requests_allowed -= 1
			piece_id,block_offset = self.torrent.file_manager.incrementPieceBlock(piece_id,block_offset)
			if(piece_id<0 or block_offset<0):
				return -1,-1

	def canRequestBlock(self, piece_id, block_offset, requests_allowed, peer):
		if(len(self.peers_requesting_blocks[piece_id][block_offset]) < requests_allowed 
			and (piece_id,block_offset) not in peer.set_of_blocks_requested 
			and (piece_id,block_offset) not in peer.set_of_blocks_received
			and peer.peer_has_pieces[piece_id] == True 
			and self.torrent.file_manager.blockExists(piece_id,block_offset) == False):
			return True
		return False

	def havePiece(self,peer,piece_index):
		if(peer.ip,peer.port not in self.peerlist_of_pieces[piece_index]):
			self.peerlist_of_pieces[piece_index][(peer.ip,peer.port)] = peer

	def haveBitfield(self,peer,bitfield):
		bitarray = BitArray(bytes=bitfield)
		for x in range(len(self.peerlist_of_pieces)):
			if(bitarray[x] == True and (peer.ip,peer.port) not in self.peerlist_of_pieces[x]):
				self.peerlist_of_pieces[x][(peer.ip,peer.port)] = peer

	def requestSuccessful(self,peer,piece_id,block_offset):
		self.total_requests += 1
		self.total_requests_sent += 1
		self.peers_requesting_blocks[piece_id][block_offset][(peer.ip,peer.port)] = peer

	def removeRequest(self, peer, piece_id, block_offset):
		if((peer.ip,peer.port) not in self.peers_requesting_blocks[piece_id][block_offset]):
			raise "ERROR: Request was never added for this "+str(peer.ip)+ " " + str(peer.port)
		del self.peers_requesting_blocks[piece_id][block_offset][(peer.ip,peer.port)]
		self.total_requests -= 1
		piece_id = self.torrent.file_manager.current_pos_piece_id
		block_offset = self.torrent.file_manager.current_block_offset
		while(self.total_requests < MAX_TOTAL_REQUESTS):
			if piece_id in self.peers_requesting_blocks:
				if block_offset in self.peers_requesting_blocks[piece_id]:
					tteemmpp = self.peers_requesting_blocks[piece_id][block_offset].keys()
					for peer in tteemmpp:
						self.peers_requesting_blocks[piece_id][block_offset][peer].generate_next_request()
						if(self.total_requests > MAX_TOTAL_REQUESTS):
							break
			piece_id,block_offset = self.torrent.file_manager.incrementPieceBlock(piece_id,block_offset)
			if piece_id == -1 and block_offset == -1 :
				break

	def cancelRemainingRequests(self,piece_id,block_offset):
		Logger.info("Cancelling Remaining Requests for: " + str(piece_id)+","+str(block_offset))
		Logger.info("Number of clients with pending requests: "+str(len(self.peers_requesting_blocks[piece_id][block_offset])))
		for peer in self.peers_requesting_blocks[piece_id][block_offset]:
			self.peers_requesting_blocks[piece_id][block_offset][peer].cancelRequestFor(piece_id,block_offset)
			self.total_requests -= 1
			self.total_requests_cancelled += 1
		self.peers_requesting_blocks[piece_id][block_offset] = dict()

	def updateTotalDataReceived(self,length):
		self.total_data_received += length

	def get_initial_request_number(self):
		a = self.divide_blocks_number
		b = self.divide_blocks_number
		c = (-1)*2*MAX_TOTAL_REQUESTS
		d = b*b - 4*a*c
		if(d < 0):
			return 8
		else:
			x1 = (-b+math.sqrt(b**2-4*a*c))/2*a
			x2 = (-b-math.sqrt(b**2-4*a*c))/2*a
			if(max(x1,x2) > 0):
				return max(x1,x2)
			else:
				return 8