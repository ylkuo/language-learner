# -*- coding: utf-8 -*-

import simplejson
import os
import urllib, urllib2
from fs_client import CLIENT_ID, CLIENT_SECRET

data_path = os.path.abspath(__file__).replace(\
		os.path.basename(__file__), '').replace(\
		os.path.abspath(__file__).split('/')[-2]+'/', 'data/')

class Location():
	"""
	Get user's location from foursquare venue API
	"""
	def __init__(self):
		self.url = 'https://api.foursquare.com/v2/'
		self.venue_to_chinese = dict()
		self.chinese_to_display = dict()
		self.read_location_category()

	def read_location_category(self, \
			category_file=data_path+'location_categories.txt'):
		fp = open(category_file, 'r')
		pre_count = 0
		for line in fp:
			sep_count = line.count('\t')
			items = line.strip('\t\n').split('|')
			if sep_count == 0:
				parent = []
				pre_count = sep_count
			elif sep_count == pre_count:
				if len(parent) > 0:
					if parent[-1][2] == sep_count:
						del parent[-1]
			elif sep_count < pre_count:
				for i in xrange(pre_count - sep_count):
					if len(parent) > 0:
						if parent[-1][2] > sep_count:
							del parent[-1]
				pre_count = sep_count
			elif sep_count > pre_count:
				pre_count = sep_count
			if len(items) == 1 and len(parent) > 0:
				self.venue_to_chinese[items[0]] = parent[-1][0]
				self.chinese_to_display[parent[-1][0]] = parent[-1][1]
			elif len(items) == 2:
				parent.append((items[1], items[0].lower(), sep_count))
				self.venue_to_chinese[items[0]] = items[1]
				self.chinese_to_display[items[1]] = items[0].lower()
			elif len(items) == 3:
				parent.append((items[1], items[2].lower(), sep_count))
				self.venue_to_chinese[items[0]] = items[1]
				self.chinese_to_display[items[1]] = items[2].lower()

	def _return_result(self, endpoint, params=None):
		"""
		Method to make query to foursquare to get result.
		Arguments (Required):
			``endpoint'': The foursquare API endpoint for this request.
		Arguments (Optional):
			``params'': Parameters that sent to API. 
						They are encoded in a dictionary.
		"""
		query_url = self.url + endpoint
		params['client_id'] = CLIENT_ID
		params['client_secret'] = CLIENT_SECRET

		data = urllib.urlencode(params)
		request = urllib2.Request('%s?%s' % (query_url, data))

		try:
			result = simplejson.load(urllib2.urlopen(request))
		except IOError, e:
			result = simplejson.load(e)
		return result

	def get_venues(self, geolat, geolong, limit=30):
		params = {'ll':geolat+','+geolong, 'limit':limit}
		venues = self._return_result('venues/search', params)[\
				'response']['groups'][0]['items']
		near_categories = []
		for venue in venues:
			for category in venue['categories']:
				if category['name'] not in self.venue_to_chinese.keys():
					continue
				chinese = self.venue_to_chinese[category['name']]
				display_name = self.chinese_to_display[chinese]
				if (chinese, display_name) not in near_categories:
					near_categories.append((chinese, display_name))
		return near_categories
			

if __name__ == '__main__':
	location = Location()
	venues = location.get_venues('42.3609385', '-71.0876401')
	for chinese, display in venues:
		print chinese+', '+display
