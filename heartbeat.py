import threading
import time
import socket
import struct
import time

from gateway import WrtGateway
import restful
import init

class HBThread(threading.Thread):
	"""docstring for HeartBeat"""
	def __init__(self,interval):
		super(HBThread, self).__init__()
		self.interval = interval

	# send heartbeat using HTTP
	def run(self):
		while True:
			print '[HBThread] uploading heartbeat'
			ret1 = restful.method_get(init.url_hb + '/' + WrtGateway.s_hwid)
			content = ret1.split('Content>')[1].split('<')[0]
			#print content
			# heartbeat interval
			time.sleep(self.interval)