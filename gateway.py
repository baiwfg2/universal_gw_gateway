#-*-coding:utf-8-*-
import random
import time
import sys
import re
import json

import restful
import init
import common
import mythread

class WrtGateway:
	# class varaiable
	s_hwid = ''
	s_mwid = ''
	s_first_time_add_dev = False

	def __init__(self,mail):
		self.hwid = ''
		self.mwid = ''
		self.mail = mail
		self.res_dict = {}
		
	def reg_hwid(self):
		# register hardware id
	
		#self.hwid = '200000'
		self.hwid = common.get_mac_addr()
		print 'hwid:',self.hwid
		WrtGateway.s_hwid = self.hwid

		if common.is_hwid_existed(self.hwid) == True:
			return
			
		body = '<RegisterHWSN><HWSN>' + self.hwid + \
			'</HWSN><User>Admin</User>'\
			'<Password>admin</Password></RegisterHWSN>'
		header = {'Content-type':'text/xml'}
		print 'registering hwid...'
		try:
			ret = restful.method_post(init.url_registerHW,body,header)
			if ret.split('>')[2].split('<')[0] == 'true':
				print 'register hwid ok'
				common.wr_settings(self.hwid,'',0)
				common.wr_settings('','',1)
		except:
			# repeating registering hwid will raise exception
			print 'hwid already exists or network off'
			common.wr_settings(self.hwid,'',0)
			common.wr_settings('','',1)
		
	def reg_mwid(self):
		# register middleware id
		
		mwid = common.is_mwid_existed(self.hwid)
		if mwid != '':
			self.mwid = mwid
			print 'mwid:',mwid
			WrtGateway.s_mwid = self.mwid
			return
			
		body = '<Verification><HWSN>' + self.hwid + '</HWSN><EmailAddress>' + self.mail + \
			'</EmailAddress><MWID></MWID></Verification>'
		header = {'Content-type':'text/xml'}
		print 'registering mwid...'
		ret = restful.method_post(init.url_registerMW,body,header)
		self.mwid = ret.split('>')[2].split('<')[0]
		WrtGateway.s_mwid = self.mwid
		print 'register mwid ok.mwid:',self.mwid
		common.wr_settings(self.mwid,'',1)
		common.wr_settings('0','',2)
			
	def update_mw(self,force_update=False):
		# I haven't add resid in this body, which can be done with other interfaces
		# but at lease one devid should be included in this body,
		# or the following call add_dev will fail

		# force_update means force updating property
		if not force_update and common.is_updated() == True:
			return

		body = common.rd_prop('cfg/gw_property.xml')
		header = {'Content-type':'text/xml'}
		print 'updating gateway property...'
		
		ret = restful.method_post(init.url_updateMW + '/' + self.mwid,body,header)
		if ret.split('>')[2].split('<')[0] == 'true':
			print 'update gateway property ok'
			common.wr_settings('1','',2)
			common.write_file('cfg/mac_dev_map.cfg','')
			common.write_file('cfg/mac_resID_resPlat_map.cfg','')

			#if force_update == True:
			#	sys.exit(0)
			# write default device '00' into the file
			#common.wr_settings('00','',2)
			
	def update_id_info(self,alias):
		body = '<IDInfo Name="标识信息"><GWName Name="网关名称">gateway</GWName>\
			<GWAlias Name="网关别名">' + str(alias) + '</GWAlias></IDInfo>'
  		header = {'Content-type':'text/xml'}
		print 'updating gateway alias to "' + str(alias) + '"'

		ret = restful.method_post(init.hostandport + '/WIFPa/UpdateIDInfo/' + 
			self.mwid + '?lang=zh',body,header)

		if ret.split('>')[2].split('<')[0] == 'true':
			pass

	def del_mw(self):
		# just delete mwid and its property not including hwid
		body = '<Verification xmlns="http://schemas.datacontract.org/2004/07/EntityLib.Entity"> \
			<EmailAddress>' + self.mail + '</EmailAddress> \
			<HWSN>' + self.hwid + '</HWSN> \
			<MWID>' + self.mwid + '</MWID></Verification>'
		header = {'Content-type':'text/xml'}
		print '\ndeleting gateway...,hwid:%s,mwid:%s' %(self.hwid,self.mwid)
		ret = restful.method_post(init.url_deleteGW,body,header)

		if ret.split('>')[1].split('<')[0] == 'true':
			print 'delete mw ok'
			# clear mwid
			common.wr_settings('','',1)
			# clear updated flag
			common.wr_settings('0','',2)
		else:
			print 'fail'
			
	@staticmethod
	# Note:if there're no any devices on platform, add_dev call then would fail !!!
	def add_dev():
		# no res default, and no need to give devid by yourself
		body = common.rd_prop('cfg/dev_property.xml')
		header = {'Content-type':'text/xml'}
		print '\nadd device...'
		ret = restful.method_post(init.url_addDevice + '/' + WrtGateway.s_mwid,body,header)
		newdevid = ret.split('>')[2].split('<')[0]

		if newdevid  == 'false':
			print 'add device failed'
			sys.exit(-1)
		if newdevid.find(',') == -1:
			print 'devid:' + newdevid + ' added'
		else:
			lst = newdevid.split(',')
			del lst[0]
			print 'resid:' + str(lst) + ' added'
		#common.wr_settings(newdevid,'',2)
		
		return newdevid
	
	@staticmethod
	def del_dev(devid):
		# It seems that it's still ok even if the devid doesn't exist
		body = ''
		header = {'Content-type':'text/xml'}
		print '\ndeleting dev...'
		
		ret = restful.method_post(init.url_delDevice + '/' + WrtGateway.s_mwid + '?devid=' + devid,body,header)
		if ret.split('>')[2].split('<')[0] == 'true':
			print 'delete devid:' + devid + ' ok'
		
	@staticmethod	
	def add_res(devid):
		body = common.rd_prop('cfg/res_property.xml')		
		header = {'Content-type':'text/xml'}

		print '\nadd resource...'	
		ret = restful.method_post(init.url_addRes + '/' + WrtGateway.s_mwid + '?devid=' + devid,body,header)
		newresid = ret.split('>')[2].split('<')[0]

		if newresid == 'false':
			print 'add resource failed'
			sys.exit(-1)
		print 'resid:' + newresid + ' newly added for ' + devid
		#common.wr_settings(newresid,devid,3)
		
		return newresid
	
	@staticmethod
	def del_res(devid,resid):
		body = ''
		header = {'Content-type':'text/xml'}
		print '\ndeleting res...'
		ret = restful.method_post(init.url_delRes + '/' + WrtGateway.s_mwid + '?devid=' + devid + '&resid=' + resid,body,header)
		if ret.split('>')[2].split('<')[0] == 'true':
			print 'delete resid:' + resid + ' for ' + devid + ' ok'
	

	# Reference page: http://121.42.31.195:9071/WIFPd/help/operations/uploadServiceData
	@staticmethod
	def upload_data(resid,data):	
		FORMAT = '%Y-%m-%dT%X'
		body = '<ServiceData><mwid>' + WrtGateway.s_mwid + '</mwid><datatime>' + \
		time.strftime(FORMAT,time.localtime()) + '</datatime><Datapoints><value>' + \
		str(data) + '</value><num>' + str(resid) + '</num></Datapoints></ServiceData>'

		header = {'Content-type':'text/xml'}	
		try:
			print 'uploading data...'
			ret = restful.method_post(init.url_uploadData + '/' + WrtGateway.s_mwid,body,header)

			if ret.split('>')[2].split('<')[0] == 'true':
				print 'upload value: ' + str(data) + ' for resid ' + str(resid) + ' ok\n'
		except:
			print 'upload_data except'
			return
		

	# Reference page: http://121.42.31.195:9071/WIFPd/help/operations/UploadImage
	@staticmethod
	def upload_image(resid,data):
		header = {'Cache-Control':'no-cache','Content-Type':'image/jpeg','Content-Length': len(data)}
		try:
			print 'uploading image...'
			ret = restful.post_image(init.url_camera + '/' + WrtGateway.s_mwid + '?ResID=' + str(resid),data,header)
			if ret.split('>')[1].split('<')[0] == 'true':
				print 'upload image data ' + 'for resid ' + str(resid) + ' ok\n'
		except:
			print 'upload_image except'
			return


	def get_sensordata(self,resid):
		ret = restful.method_get(init.url_sensorData + '/' + self.mwid + '?ResourceID=' + str(resid))
		print 'get value for resid',resid,':',ret.split('<resvalue>')[1].split('</resvalue')[0]

	# read dev_property.xml and create dict mapping. Finally write the dict to resource list file
	# for other application's use
	# self.res_dict's format is like this:
	# key:the resource name provided in dev_proerty.xml
	# value: is a list of two element. First is the flag which denotes whether the resource is 
	#		 character-based(0) or image-based(1)
	#		 Second one is resource's id, allocated by WoT platform
	def get_dev_property(self):
		devid = WrtGateway.add_dev()
		resid = devid.split(',')

		metadata = common.read_file('cfg/dev_property.xml')
		resources = re.findall(r'<Resource[^s].*</Resource>',metadata,re.S)[0]
		data = resources.split('<Resource')

		for i in range(1,len(data)):
			lst = []
			data_type = re.findall(r'<Type.*</Type>',data[i])[0]
			type_value = data_type.split('>')[1].split('<')[0]
			lst.append(type_value)
			lst.append(resid[i])

			name = re.findall(r'".*"',data[i])[0].split('"')[1]

			self.res_dict[name] = lst
			common.write_file('res_list.txt',json.dumps(self.res_dict))
		print 'res_dict:',self.res_dict
		print

	# This method is worse than get_dev_property in performance and should be deprecated.
	def read_dev_property(self):
		metadata = common.read_file('cfg/dev_property.xml')
		resources = re.findall(r'<Resource[^s].*</Resource>',metadata,re.S)[0]
		
		str_pos = metadata.find("Resource Name");
		first_str = metadata[:(str_pos-1)]

		last_str = re.findall(r'</Resources.*',metadata,re.S)[0]
		devid = WrtGateway.add_dev()
		
		data = resources.split('<Resource')
		resid = devid.split(',')

		replace_str = '<Resource'
		for i in range(1,len(data)):
			lst = []
			url_sensor  = init.url_sensorData + '/' + self.mwid + '?ResourceID=' + str(resid[i])
			url_image = 'http://121.42.31.195:9071/WIFPa/GetImage/' + self.mwid + '?ResID=' + str(resid[i])

			url_prefix = re.findall(r'<Url.*">',data[i])[0]
			url_suffix = re.findall(r'</Url>.*>',data[i],re.S)[0]
			data_type = re.findall(r'<Type.*</Type>',data[i])[0]

			type_value = data_type.split('>')[1].split('<')[0]
			
			lst.append(type_value)
			lst.append(resid[i])
				
			pos = data[i].find(url_prefix)

			if type_value == '0':
				data[i] = data[i][:(pos+len(url_prefix))] + url_sensor + url_suffix
			elif type_value == '1':
				data[i] = data[i][:(pos+len(url_prefix))] + url_image + url_suffix
			else:
				data[i] = data[i][:(pos+len(url_prefix))] + url_suffix

			name = re.findall(r'".*"',data[i])[0].split('"')[1]
			self.res_dict[name] = lst

			if i == (len(data)-1):
				replace_str = replace_str + data[i]
			else:
				replace_str = replace_str + data[i] + '\n<Resource'

		#print 'first_str:\n',first_str
		#print 'replace_str:\n',replace_str
		#print 'last_str:\n',last_str

		metadata = first_str + replace_str + last_str
		#print 'debug:',metadata
		common.write_file('cfg/dev_property.xml',metadata)
		print 'res_dict:',self.res_dict

