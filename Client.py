import magnetToTorrent as Magnet
import Torrent
import gzip
import os
import urllib2
import urllib
import hashlib
import requests
import logging as Logger
from struct import *
from twisted.internet import reactor
import socket,struct
import time
import Core
import thread
from Tkinter import *
from tkFileDialog import askopenfilename
import sys
import select,errno
from sys import stdout

flag = 0

def callback():
    text = e.get()
    print text
    flag=1
    main(text)

def donothing():
   filewin = Toplevel(root)
   button = Button(filewin, text="Do nothing button")
   button.pack()

def quit_handler():
    print "program is quitting!"
    sys.exit(0)

def open_file_handler():
    file= askopenfilename()
    flag = 0
    main(file)

def init_log():
	Logger.basicConfig(filename='BTP5_LOG.log',
							filemode='a',
							format='%(asctime)s : %(message)s',
							level=Logger.INFO)
	print "in log"
	Logger.info("Client Started.\nLog Initialized")
'''
def reconnect(client):
	peer_by_tracker = dict()
	t1 = time.time()
	while(True):
		if(time.time() - t1 > 60):	#TODO: Add a min threhshold for number of peers
			#busy waiting
			Logger.info("Now Refreshing Trackers for Peer List")
			Logger.info("Reconnecting to tracker for additional peers.")
			peer_by_tracker = client.torrent.start()
			for peer_tuple in peer_by_tracker:
				peers = peer_by_tracker[peer_tuple][1]
				for x in xrange(len(peers)):
					if client.torrent.protocol.has_peer(peers[x]['IP'],peers[x]['port']) == False:
						Logger.info("Sending request to peer" + str(peers[x]['IP']) + str(peers[x]['port'])) 
						reactor.connectTCP(socket.inet_ntoa(struct.pack("!i",peers[x]['IP'])), peers[x]['port'], client.torrent.protocol)
			t1 = time.time()	#resetting the timer
'''

class Client(object):
	def __init__(self,*args):
		self.peerID = self.generatePID()
		self.port = 6888
		if flag == 1:
			self.initAll(*args)
		elif flag == 0:
			self.initAl(*args)
	def generatePID(self):
		ret = "MKR_" + str(os.getpid()) + str(os.times()[-1])
		ret = pack('20s', ret[:20])
		Logger.info("Peer ID Generated :" + str(ret))
		return ret
	def initAll(self,torrent_link):
		Logger.info("Initializing Torrent Data")
		torrent_raw_data  = self.downloadTorrentFile(torrent_link)
		self.torrent = Torrent.Torrent(raw_data = torrent_raw_data, peer_id = self.peerID, port = self.port)
		Logger.info("Initialization For Torrent Data Complete")
	def initAl(self,torrent1):
		torrent_raw_data1 = self.readtorrent(torrent1)
		self.torrent = Torrent.Torrent(raw_data = torrent_raw_data1, peer_id = self.peerID, port = self.port)
		Logger.info("Initialization For Torrent Data Complete")

	def downloadTorrentFile(self,torrent_link):
		Logger.info("Now Downloading Torrent File")
		url = torrent_link
		#f = urllib2.urlopen(url)
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		response = opener.open(url)
		temp_torrent_filename = "tempTorrentFile.torrent.gz"
		data = response.read()			
		try:								
			#download the torrent file pointed to by the url.
			with open(temp_torrent_filename, "wb") as code:
				code.write(data)					
			#save it in a temp file.
			f = gzip.open(temp_torrent_filename,'rb')
			file_content = f.read()									
			#unzip it to extract original contents and delete this temp file.
			os.remove(temp_torrent_filename)
		except:
			file_content = data
		Logger.info("Torrent File Download Complete")
		return file_content
	
	def readtorrent(self,torrent):
		f1 = open(torrent, 'r')
		file_content1 = f1.read()
		#print file_content1
		f1.close()
		return file_content1	
		#with open(torrent,'r') as myfile:
		#	file_content = myfile.read()					

	def getTotalLength(self):
		if('files' in self.torrent.info):
			listofFiles = self.torrent.info['files']
			total = 0
			for files in listofFiles:
				total += files['length']
			return total
		else:
			return self.torrent.info['length']

def main(link):
	init_log()
	#client = Client("http://torcache.net/torrent/BCF27930087EAA422413B02650B55BB2A9567C49.torrent?title=[kickass.to]eminem.the.marshall.mathers.lp2.deluxe.edition.2013.320kbps.cbr.mp3.vx.p2pdl")	
	#client = Client("http://torcache.net/torrent/A7C04E9C66061C5C0E66FC2C61BA5A28D819F0AD.torrent?title=[kickass.to]linkin.park.greatest.hits.2013")
	#client = Client("http://torcache.net/torrent/B22B8FC4068C723EF8FE59540DC7199A9AA7D738.torrent?title=[kickass.to]queen.2014.hindi.320kbps.vbr.mp3.songs.praky")
	#client = Client("https://torcache.net/torrent/D3FB00BF8DD7498A7DE8D974A05B450E8187D07C.torrent?title=[kat.cr]drake.views.2016.mp3")
	#client = Client("https://archive.org/download/testmp3testfile/testmp3testfile_archive.torrent")
	#client = Client("https://torcache.net/torrent/2DC75EEFE0DA8D24F1C343CEB48E00FD0C1E4563.torrent?title=[kat.cr]homemade.muscle.all.you.need.is.a.pull.up.bar.1st.edition.2015.epub.gooner")
	#client = Client("https://torcache.net/torrent/6C91EC5A415F2192ADB163D2FC75F172E07A7B0D.torrent?title=[kat.cr]brain.training.how.to.learn.and.remember.everything")
	
	client =  Client(link)

	peer_by_tracker = dict()
	peer_by_tracker = client.torrent.start()
	Logger.info("Now Connecting to Peers")
	for peer_tuple in peer_by_tracker :
		peers = peer_by_tracker[peer_tuple][1]
		if(peers == None):
			continue
		x = 0
		for x in xrange(len(peers)):
			if(x < 60):
				reactor.connectTCP(socket.inet_ntoa(struct.pack("!i",peers[x]['IP'])), peers[x]['port'], client.torrent.protocol)
	reactor.run()


root = Tk()
menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="New", command=donothing)
filemenu.add_command(label="Add Torrent File", command=open_file_handler)
filemenu.add_command(label="Save", command=donothing)
filemenu.add_command(label="Save as...", command=donothing)
filemenu.add_command(label="Close", command=quit_handler)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)
editmenu = Menu(menubar, tearoff=0)
editmenu.add_command(label="Undo", command=donothing)
editmenu.add_separator()
editmenu.add_command(label="Cut", command=donothing)
editmenu.add_command(label="Copy", command=donothing)
editmenu.add_command(label="Paste", command=donothing)
editmenu.add_command(label="Delete", command=donothing)
editmenu.add_command(label="Select All", command=donothing)
menubar.add_cascade(label="Edit", menu=editmenu)
helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help Index", command=donothing)
helpmenu.add_command(label="About...", command=donothing)
menubar.add_cascade(label="Help", menu=helpmenu)
open_file = Button(root, command=open_file_handler, padx=100, text="OPEN FILE")
open_file.pack()
e = Entry(root)
e.pack()
e.focus_set()
b = Button(root, text="Download Torrent", width=10, command=callback)
b.pack()
text = e.get()
quit_button = Button(root, command=quit_handler, padx=100, text="QUIT")
quit_button.pack()
root.config(menu=menubar)
root.mainloop()



