# -*- coding: utf-8 -*

import os

lib_path = os.path.abspath(__file__).replace(\
		os.path.basename(__file__), '').replace(\
		os.path.abspath(__file__).split('/')[-2]+'/', 'lib/')

def get_pinyin(text):
	cmd = 'echo "%s" | %sadso/adso -y -n' % (text, lib_path)
	f = os.popen(cmd.encode('utf-8'))
	output = f.readline().strip()
	return output

if __name__ == '__main__':
	text = u'蘋果'
	print get_pinyin(text).lower()
