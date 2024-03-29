# -*- coding: utf-8 -*

import sys, os
import divisi2
import MySQLdb
from bing_translate import BingTranslate
from collections import defaultdict
from config_client import DB_SERVER, DB_NAME, DB_USER, DB_PASSWD
from conceptnet_api import get_assertions
from concept_category import ConceptCategory
from context import Location
from sklearn.cluster import AffinityPropagation
from util import cosine_similarity

data_path = os.path.abspath(__file__).replace(\
		os.path.basename(__file__), '').replace(\
		os.path.abspath(__file__).split('/')[-2]+'/', 'data/')

path = os.path.abspath(__file__).replace(\
        os.path.basename(__file__), '')

class Database:
	def __init__(self, is_debug=0):
		# define db
		self.server = DB_SERVER
		self.DB_username = DB_USER
		self.password = DB_PASSWD
		self.database = DB_NAME
		self.cursor = self.link_db(is_debug)
		if not self.cursor:
			print "Error linking database...exit"
			exit()
		return

	def link_db(self, is_debug=0):
		db = MySQLdb.connect(host=self.server, user=self.DB_username, \
					passwd=self.password, db=self.database, \
					use_unicode = True, charset = "utf8")
		self.cursor = db.cursor()
		return self.cursor

	def query_db(self, cmd, is_debug=0):
		try:
			self.cursor.execute(cmd) 
			result = self.cursor.fetchall()
		except (AttributeError, MySQLdb.OperationalError):
			self.cursor = self.link_db(is_debug)
			self.cursor.execute(cmd) 
			result = self.cursor.fetchall()
		return result

def add_concepts(matrix_path=data_path+'feature_matrix_zh.smat'):
	A = divisi2.load(matrix_path)
	db = Database()
	for concept in A.row_labels:
		num_word = len(' '.join(concept).split())
		num_assertion = len(A.row_named(concept).keys())
		cmd = u"INSERT INTO concept (name, num_word, num_assertion) \
		       VALUES ('%s', %d, %d)" % (concept, num_word, num_assertion)
		db.query_db(cmd)

def rank_concepts():
	db = Database()
	cmd = "SELECT MAX(num_word) FROM concept"
	concept_res = db.query_db(cmd)
	max_num_word = int(concept_res[0][0])
	cmd = "SELECT * FROM concept"
	concept_res = db.query_db(cmd)
	for concept in concept_res:
		id, name, num_word, num_assertion, difficulty = concept
		difficulty = (float(num_word)/float(max_num_word)) * \
				(1.0/float(num_assertion))
		cmd = "UPDATE concept SET difficulty = %lf WHERE id = %s" \
				% (difficulty, id)
		db.query_db(cmd)

def add_locations():
	location = Location()
	db = Database()
	for chinese, display in location.chinese_to_display.items():
		cmd = u"SELECT * FROM location WHERE chinese_name = '%s'" \
				% (chinese.decode('utf-8'))
		location_res = db.query_db(cmd)
		if len(location_res) == 0:
			cmd = u"INSERT INTO location (name, chinese_name) \
					VALUES ('%s', '%s')" % \
					(display.decode('utf-8'), chinese.decode('utf-8'))
			db.query_db(cmd)

def update_location_actions():
	from re import escape
	location = Location()
	db = Database()
	t = BingTranslate()
	cmd = "SELECT * FROM location"
	location_res = db.query_db(cmd)
	for item in location_res:
		location_id, location_name, location_chinese = item
		for action in location.get_action_for_venue(location_chinese):
			cmd = u"SELECT * FROM action WHERE chinese_name = '%s'" \
					% (action)
			action_res = db.query_db(cmd)
			if len(action_res) > 0:
				action_id = action_res[0][0]
				is_bad = action_res[0][3]
			else:
				action_en = t.translate(action, "zh-CHT", "en")
				cmd = u"INSERT INTO action (chinese_name, english_name) \
						VALUES ('%s', '%s')" % \
						(escape(action), escape(action_en))
				db.query_db(cmd)
				cmd = u"SELECT * FROM action WHERE chinese_name = '%s'" \
						% (action)
				action_res = db.query_db(cmd)
				action_id = action_res[0][0]
				is_bad = action_res[0][3]
			if is_bad != 1:
				cmd = "INSERT INTO location_action (location_id, action_id) \
						VALUES (%s, %s)" % (location_id, action_id)
				db.query_db(cmd)

def update_location_concepts():
	"""
	Get related concepts of a location and store it in database.
	"""
	location = Location()
	db = Database()
	cmd = "SELECT * FROM location"
	location_res = db.query_db(cmd)
	for item in location_res:
		location_id, location_name, location_chinese = item
		for concept in location.get_concept_for_venue(location_chinese):
			cmd = u"SELECT * FROM concept WHERE name = '%s'" \
					% (concept)
			concept_res = db.query_db(cmd)
			if len(concept_res) > 0:
				concept_id = concept_res[0][0]
				is_bad = concept_res[0][8]
			else:
				continue
			if is_bad != 1:
				cmd = "INSERT INTO location_concept (location_id, concept_id) \
						VALUES (%s, %s)" % (location_id, concept_id)
				db.query_db(cmd)

def update_action_concepts():
	"""
	Get related concepts of an action and store it in database.
	"""
	location = Location()
	db = Database()
	cmd = "SELECT * FROM action"
	action_res = db.query_db(cmd)
	for item in action_res:
		action_id, action_chinese, action_english, is_bad = item
		if is_bad == 1:
			continue
		for concept in location.get_concept_for_venue(action_chinese):
			cmd = u"SELECT * FROM concept WHERE name = '%s'" \
					% (concept)
			concept_res = db.query_db(cmd)
			if len(concept_res) > 0:
				concept_id = concept_res[0][0]
				is_bad = concept_res[0][8]
			else:
				continue
			if is_bad != 1:
				cmd = "INSERT INTO action_concept (action_id, concept_id) \
						VALUES (%s, %s)" % (action_id, concept_id)
				db.query_db(cmd)

def cluster_concepts(context='location'):
	"""
	Cluster related concepts of a specific type to different categories
	"""
	db = Database()
	concept_category = ConceptCategory()
	cmd = "SELECT * FROM %s" % (context)
	context_res = db.query_db(cmd)
	concept_list = []
	concept_matrix = []
	for item in context_res:
		concept_list = []
		concept_matrix = []
		if context == 'action':
			context_id, context_chinese, context_name = item[:3]
		elif context == 'location':
			context_id, context_name, context_chinese = item
		cmd = "SELECT b.name, b.id FROM %s_concept AS a, concept AS b \
				WHERE a.%s_id = %s AND a.concept_id = b.id" \
				% (context, context, context_id)
		concept_res = db.query_db(cmd)
		if len(concept_res) == 0:
			continue
		for item in concept_res:
			concept, concept_id = item
			concept_vector = concept_category.concept_axes.row_named(concept)
			concept_list.append((concept_id, concept))
			concept_matrix.append(concept_vector)
		# Run affinity propogation
		S = cosine_similarity(concept_matrix, concept_matrix)
		af = AffinityPropagation()
		af.fit(S)
		cluster_centers_indices = af.cluster_centers_indices_
		labels = af.labels_
		count = 0
		clusters = defaultdict(list)
		for label in labels:
			clusters[\
				concept_list[cluster_centers_indices[label]][1]].append(\
				concept_list[count])
			count += 1
		category_num = 0
		for key, value in clusters.items():
			category_num += 1
			for concept in value:
				cmd = "UPDATE %s_concept SET category = %d WHERE \
						%s_id = %s AND concept_id = %s" \
						% (context, category_num, context, \
						context_id, concept[0])
				db.query_db(cmd)
				print concept[1].encode('utf-8')+' ',
			print ''
		print '----------'+context_chinese.encode('utf-8')+'----------'

def download_concept_image():
	"""
	Download and update image file path for each concept.
	"""
	from image import Image
	db = Database()
	image = Image()
	cmd = 'SELECT * FROM concept'
	concept_res = db.query_db(cmd)
	for concept in concept_res[92606:]:
		concept_id = concept[0]
		concept_name = concept[1]
		filename = image.get_image(concept_name, \
				str(concept_id), path+'static/img/concept/')
		cmd = 'UPDATE concept SET image_file = "%s" WHERE id = %s' \
				% (filename, concept_id)
		db.query_db(cmd)
		
def download_concept_audio():
	"""
	Download audio wav file for each concept.
	"""
	db = Database()
	t = BingTranslate()
	cmd = 'SELECT * FROM concept'
	concept_res = db.query_db(cmd)
	for concept in concept_res[117599:]:
		concept_id = concept[0]
		concept_name = concept[1]
		filename = path+'static/audio/concept/'+str(concept_id)+'.wav'
		print filename
		t.get_speech(concept_name, filename, "zh-CHT")

def update_concept_pinyin():
	from pinyin import get_pinyin
	db = Database()
	cmd = 'SELECT * FROM concept'
	concept_res = db.query_db(cmd)
	for concept in concept_res:
		concept_id = concept[0]
		concept_name = concept[1]
		pinyin = get_pinyin(concept_name).lower()
		cmd = 'UPDATE concept SET pinyin = "%s" WHERE id = %s' \
				% (pinyin, concept_id)
		db.query_db(cmd)

def update_concept_english():
	db = Database()
	t = BingTranslate()
	cmd = 'SELECT * FROM concept'
	concept_res = db.query_db(cmd)
	for concept in concept_res[90835:]:
		concept_id = concept[0]
		concept_name = concept[1]
		english = t.translate(concept_name, "zh-CHT", "en").lower()
		print english.encode('utf-8')
		cmd = 'UPDATE concept SET english = "%s" WHERE id = %s' \
				% (english, concept_id)
		db.query_db(cmd)

if __name__ == '__main__':
	#add_locations()
	#update_location_actions()
	#update_location_actions()
	#update_location_concepts()
	#update_action_concepts()
	#cluster_concepts('location')
	cluster_concepts('action')
	#download_concept_image()
	#download_concept_audio()
	#update_concept_english()
