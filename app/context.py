# -*- coding: utf-8 -*-

import simplejson
import urllib, urllib2
from fs_client import CLIENT_ID, CLIENT_SECRET

class Location():
	"""
	Get user's location from foursquare venue API
	"""
	def __init__(self):
		self.url = 'https://api.foursquare.com/v2/'

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

	def get_venues(self, geolat, geolong, limit=5):
		params = {'ll':geolat+','+geolong, 'limit':limit}
		venues = self._return_result('venues/search', params)[\
				'response']['groups'][0]['items']
		for venue in venues:
			for category in venue['categories']:
				return category['name']
			

if __name__ == '__main__':
	location = Location()
	print location.get_venues('42.3609385', '-71.0876401')
