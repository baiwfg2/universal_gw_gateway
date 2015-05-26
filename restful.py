import urllib2
import base64
import requests

def method_post(url,data,header):
	#print 'url:',url
	req = urllib2.Request(url,data,header)
	resp = urllib2.urlopen(req)
	return resp.read()
	
def method_get(url):
	req = urllib2.Request(url)
	resp = urllib2.urlopen(req)
	return resp.read()

# This method can be used to post an image to SAE web application 
def method_post_image(url,image_bytes):
	encoded_image = base64.b64encode(image_bytes)
	#print 'encoded_image:',encoded_image
	#params = urllib.urlencode(raw_params)
	request = urllib2.Request(url, encoded_image)
	page = urllib2.urlopen(request)

def post_image(url,imagebytes,header):
	response = requests.post(url,data=imagebytes,headers=header)
	return response.content