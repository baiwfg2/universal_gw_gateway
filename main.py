# coding=utf-8
# This is a Web of Things Middleware written with Python programming 
# language. It mainly provides the function of gateway registration,
# device/resource registration, data uploading, heartbeat uploading and
# so on.

# Authors: Chen Shi & Yang Ping (BUPT MineLab-818)

import sys
import time
import json
import urllib

import init
import common
from gateway import WrtGateway
from heartbeat import HBThread

#from camera_thread import CameraThread

F_DEL_MW = False
F_UPT_MW = False

# prevent the error: 'ascii' codec can't decode byte, which will happen when aj-server
# send data
reload(sys)
sys.setdefaultencoding('utf8')

def parse_para():
	
	global F_DEL_MW
	global F_UPT_MW

	for i in range(1,len(sys.argv)):
		if sys.argv[i] == '-d':
			F_DEL_MW = True

		elif sys.argv[i] == '-upt':
			F_UPT_MW = True

		elif sys.argv[i] == '-h':
			print 'available options:'
			print '-d\tdelete gateway'
			print '-upt\tforce update gateway property'
			sys.exit(0)

		else:
			print 'illegal parameter'
			sys.exit(-1)

if __name__ == '__main__':
	# parse prompt parameter
	parse_para()

	init.rd_local_cfg()

	# mail is given
	gw = WrtGateway('mail')	
	# if hwid exists,then it will fail
	gw.reg_hwid()

	# register mwid, which is given by platform according to email and hwid
	gw.reg_mwid()

	if F_DEL_MW:
		gw.del_mw()
		sys.exit(0)

	# update property of gateway
	gw.update_mw(F_UPT_MW)

	# read the device and resources configurations made by middleware users
	gw.get_dev_property()
	
	hb_thread = HBThread(5)
	hb_thread.start()

	while True:
		# 防止读的时候，另一进程只写了部分数据
		while True:
			try:
				jsondata = json.loads(common.read_file("data.txt"))
				time.sleep(1)
				break
			except:
				pass

		print 'jsondata:',jsondata
		print

		for name in gw.res_dict.keys():
			if jsondata.has_key(name):
				lst = gw.res_dict[name]
				if lst[0] == '0':
					# 传字符
					gw.upload_data(lst[1],str(jsondata[name]))
					#gw.get_sensordata(lst[1])
				elif lst[0] == '1':
					# 传图片
					gw.upload_image(lst[1],common.read_image(str(jsondata[name])))
				else:
					pass
				time.sleep(2)
		time.sleep(20)

	hb_thread.join()