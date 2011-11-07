# -*- coding: utf-8 -*-

import sys, os
import urllib, urllib2
from config_client import BING_ID
from urllib2 import Request, urlopen, URLError, HTTPError
from xml.dom.minidom import parseString

class BingTranslate:
	def __init__(self):
		self.appid = BING_ID
		self.base_uri = "http://api.microsofttranslator.com/V2/Http.svc"

	def _read_from_req(self, req):
		try:
			response = urllib2.urlopen(req)
			result = response.read()
			result = parseString(result).documentElement.firstChild.nodeValue
		except HTTPError, e:
			result=""
		return result

	def _download(self, req, filename):
		try:
			response = urllib2.urlopen(req)
			fp = open(filename, 'w')
			fp.write(response.read())
			response.close()
			fp.close()
			return True
		except HTTPError, e:
			print e
			return False

	def translate(self, text, fr="en", to="zh-CHT"):
		uri = "%s/Translate?appId=%s&from=%s&to=%s&text=%s" % (self.base_uri, \
			self.appid, fr, to, text.encode('utf-8'))
		req = urllib2.Request(uri)
		return self._read_from_req(req)

	def get_speech(self, text, filename, lang="zh-CHT"):
		uri = "http://translate.google.com/translate_tts?tl=%s&q=%s" \
			% (lang, text.encode('utf-8'))
		uri = "%s/Speak?appId=%s&language=%s&text=%s" % (self.base_uri, \
			self.appid, lang, text.encode('utf-8'))
		req = urllib2.Request(uri, None, {'Content-Type':'audio/wav'})
		return self._download(req, filename)


if __name__ == "__main__":
	t = BingTranslate()
	print t.translate("test").encode('utf-8')
	print t.translate(u"這是一支筆", "zh-CHT", "en")
	print t.get_speech(u"這是一支筆", "test.wav", "zh-CHT")
