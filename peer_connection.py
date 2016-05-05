import binascii, urllib, socket, random, struct
import logging

def peer_connect(payload,peer):
	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	sock.settimeout(5)
	logging.debug("Socket created")
	logging.debug("Connecting to peer "+str(peer[0])+" "+str(peer[1]))
	try:
		sock.connect(peer)
	except socket.error, msg:
		logging.debug("Error in connecting socket.")
		return 0
	logging.debug("Peer Connection successful. Now Sending Handshake.")
	req = handshake_request(payload)
	try:
		sock.sendall(req)
	except socket.error:
		logging.debug("Error in sending handshake_request")
		return 0
	logging.debug("Handshake Sent. Waiting For Response")
	try:
		buf = sock.recv(2048)
	except socket.error:
		logging.debug("Error in receiving handshake_response")
		return 0
	logging.debug("Response Received")
	return handshake_response(buf,payload)

def handshake_request(payload):
	buf = ""
	pstr = "BitTorrent protocol"
	buf += struct.pack("!b", len(pstr))
	buf += struct.pack("!19s", pstr) 									#string identifier of the protocol
	buf += struct.pack("!q", 0x0) 										#reserved bytes default to 0
	buf += struct.pack("!20s", urllib.unquote(payload['info_hash'])) 	#the info hash of the torrent we announce ourselves in
	buf += struct.pack("!20s", urllib.unquote(payload['peer_id'])) 		#the peer_id we announce
	return buf

def handshake_response(buf,payload):
	if(len(buf) < 2):
		logging.debug("Response received in handshake has length less than 2")
		return 0
	offset = 0
	pstrlen = struct.unpack_from("!b", buf, offset)[0]
	offset += 1
	pstr = struct.unpack_from("!"+str(pstrlen)+"s", buf, offset)[0]
	offset += pstrlen
	reserved = struct.unpack_from("!q", buf, offset)[0]
	offset += 8
	hash_value = struct.unpack_from("!20s", buf, offset)[0]
	offset += 20
	peer_id = struct.unpack_from("!20s", buf, offset)[0]
	offset += 20
	if (urllib.quote(hash_value) != payload['info_hash']):
		logging.debug("Hash Did Not Match")
		logging.debug(urllib.quote(hash_value))
		logging.debug(payload['info_hash'])
		return 0
	return 1
