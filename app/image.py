# -*- coding: utf-8 -*-

import urllib2
from config_client import BING_ID
from pybing import Bing

class Image():
	def __init__(self):
		self.bing = Bing(BING_ID)

	def _download(self, url, filename, content_type):
		try:
			req = urllib2.Request(url.encode('utf-8'), None, \
					{'Content-Type':content_type})
			response = urllib2.urlopen(req)
			fp = open(filename, 'w')
			fp.write(response.read())
			response.close()
			fp.close()
			return True
		except:
			return False

	def get_image(self, concept, filename, dirname):
		response = self.bing.search_image(concept.encode('utf-8'))
		if 'Image' not in response['SearchResponse'].keys():
			return None
		if 'Results' not in response['SearchResponse']['Image'].keys():
			return None
		for result in response['SearchResponse']['Image']['Results']:
			image_url = result['MediaUrl']
			thumbnail_url = result['Thumbnail']['Url']
			extension = image_url.split('.')[-1].split('&')[0].split('?')[0]
			content_type = result['Thumbnail']['ContentType']
			new_filename = filename+'.'+extension
			print new_filename.encode('utf-8')
			if self._download(thumbnail_url, dirname+new_filename, content_type) is True:
				return new_filename
			else:
				continue

if __name__ == "__main__":
	image = Image()
	print image.get_image(u'教授', 'test', 'static/img/concept/')
