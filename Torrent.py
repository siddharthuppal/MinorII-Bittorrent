import tracker_request_scrape as Scraper
import bencode
import hashlib
import urllib2
import urllib
import tracker_announce as TrackerAnnounce
import peer_connection
import socket,struct
import Core
import Messages
import logging as Logger
import math
from bitstring import BitArray
import Constants
import RequestManager
import FileManager
import RequestManager
import time


class Torrent(object):
	"""Object that Stores Torrent"""
	def __init__(self, peer_id, port, raw_data = None, torrent_dict = None):
		super(Torrent, self).__init__()
		if(raw_data == None and torrent_dict == None):
			Logger.error("Not Enough Information to get Torrent Data.\nCannot Ignore Error. Program will now Terminate")
		elif (torrent_dict == None and raw_data != None):
			torrent_dict = bencode.bdecode(raw_data)

		self.start_time 	= time.time()
		self.comment 		= torrent_dict['comment']
		self.info 			= torrent_dict['info']
		self.announce_list 	= torrent_dict['announce-list']
		self.announce 		= torrent_dict['announce']
		self.payload 		= self.generate_payload(peer_id, port)
		self.protocol 		= Core.BitTorrentFactory(self)
		self.file_manager 	= FileManager.FileManager(self.info)
		self.requester 		= RequestManager.RequestManager(self)
		
		# Stores a list of all the peers by the Tracker { ({leech, interval, seeds}, [ {IP,Port},{IP,Port}..... ]), -do- }
		self.peer_by_tracker = dict()

		# The handhshake message to be sent is constant for a given torrent 
		# str() has been overloaded
		self.handshake_message = str(Messages.Handshake(self.payload['info_hash'], self.payload['peer_id'])) 
		# Initialize the Byte And Bit Arrays for status of each piece and Block
		# self.create_piece_block_arrays(self.info['piece length'],self.getTotalLength()) 
		print "Total number of pieces :", len(self.info['pieces'])


	def generate_payload(self, peer_id, port):
		Logger.debug("Generating Payload for Torrent")
		payload = dict()
		encoded_info_dict 		= str(bencode.bencode(self.info))
		hash_obj 				= hashlib.sha1(encoded_info_dict)
		payload['info_hash'] 	= urllib.quote(str(hash_obj.digest()))
		payload['left'] 		= urllib2.quote(str(self.getTotalLength()), '')
		payload['peer_id'] 		= urllib2.quote(str(peer_id), '')
		payload['port']  		= urllib2.quote(str(port),'')
		payload['event'] 		= urllib2.quote("started",'')
		payload['uploaded'] 	= urllib2.quote("0",'')
		payload['downloaded'] 	= urllib2.quote("0",'')
		Logger.debug("Payload Generation Complete")
		return payload

	# def create_piece_block_arrays(self, piece_length, total_length):
	# 	self.no_of_blocks 	= int(math.ceil(piece_length/Constants.BLOCK_SIZE))
	# 	self.no_of_pieces 	= int(math.ceil(total_length/piece_length))
	# 	self.pieces_status 	= BitArray(self.no_of_pieces)
	# 	self.block_status 	= list()
	# 	print "Number of Pieces :", self.no_of_pieces
	# 	for x in xrange(self.no_of_pieces-1):
	# 		self.block_status.append(bytearray(self.no_of_blocks))
	# 	last_piece_size = total_length - piece_length*(self.no_of_pieces-1)
	# 	self.block_status.append(BitArray(int(math.ceil(last_piece_size/Constants.BLOCK_SIZE))))

	def getTotalLength(self):
		if('files' in self.info):
			listofFiles = self.info['files']
			total = 0
			for files in listofFiles:
				total += files['length']
			return total
		else:
			return self.info['length']

	# def bitarray_of_block_number(self):
	# 	block_number = 0
	# 	for piece in self.file_downloading.piece_list:
	# 		block_number += piece.block_number
	# 	return BitArray(block_number)

	# def determine_piece_and_block_nums(self, overall_block_num):
	# 	piece_num, block_index_in_piece  = self.overall_index_to_piece_and_index(overall_block_num)
	# 	block_byte_offset = self.block_index_to_bytes(block_index_in_piece)
	# 	return piece_num, block_byte_offset


	def start(self):
		# Connect to tracker and retrieve all the peers
		peer_list = self.connectToTracker()
		return peer_list


	"""
		Connects to the Trackers of the given Torrent File and returns a list of Seeds and Peers
	"""
	def connectToTracker(self):
		payload = self.payload
		# Returns a Dictionary of keys as Trackers and Items as ( {leech, interval, seeds}, [ {IP,Port},{IP,Port}..... ])
		peer_dict_by_tracker = self.getPeerList(payload) 
		return peer_dict_by_tracker
		
		

	def getScarpeInformation(self, payload):
		ret = dict()
		for tracker in self.announce_list:
			val = Scraper.scrape( tracker[0],[payload['info_hash']])
			if val != None:
				ret[tracker[0]] = val[payload['info_hash']]
			Logger.debug(str(tracker[0] + " :" + str(val)))
		return ret

	def getPeerList(self,payload):
		Logger.info("Getting Peer List from Trackers")
		ret = dict()
		for tracker in self.announce_list:
			val = TrackerAnnounce.announce_udp( tracker[0],payload)
			if val != None:
				ret[tracker[0]] = val
			# Logger.debug(str(tracker[0] + " :"+ str(val)))
		return ret