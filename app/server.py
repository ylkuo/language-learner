# -*- coding: utf-8 -*-

import flask
import os, re, sys
import simplejson
from bing_translate import BingTranslate
from context import Location
from database import Database

app = flask.Flask(__name__)

if len(sys.argv) == 1:
    root = 'language-learner'
else:
    root = sys.argv[1]

app_path = os.path.abspath(__file__).replace(\
		os.path.basename(__file__), '').replace(\
		os.path.abspath(__file__).split('/')[-2]+'/', 'app/')

db = Database()

def get_action_concept_category(concept):
	cmd = "SELECT a.action_id, a.category FROM action_concept AS a, \
			concept AS b WHERE a.concept_id = b.id AND b.name = '%s'" % (concept)
	action_res = db.query_db(cmd)
	return action_res

def get_location_concept_category(concept):
	cmd = "SELECT a.location_id, a.category FROM location_concept AS a, \
			concept AS b WHERE a.concept_id = b.id AND b.name = '%s'" % (concept)
	location_res = db.query_db(cmd)
	return location_res

def add_dialog(dialog, difficulty, action_category, location_category):
	cmd = "SELECT * FROM dialog WHERE content = \"%s\"" % (dialog)
	dialog_res = db.query_db(cmd)
	if len(dialog_res) == 0:
		cmd = "INSERT INTO dialog (content, difficulty) VALUES (\"%s\", %lf)" \
				% (dialog, difficulty)
		db.query_db(cmd)
		cmd = "SELECT * FROM dialog WHERE content = \"%s\"" % (dialog)
		dialog_res = db.query_db(cmd)
	dialog_id = dialog_res[0][0]
	for category in action_category:
		cmd = "INSERT INTO dialog_action_category \
				(dialog_id, action_id, category) VALUES (%s, %s, %s)" \
				% (dialog_id, category[0], category[1])
		db.query_db(cmd)
	for category in location_category:
		cmd = "INSERT INTO dialog_location_category \
				(dialog_id, location_id, category) VALUES (%s, %s, %s)" \
				% (dialog_id, category[0], category[1])
		db.query_db(cmd)

@app.route('/'+root+'/location/<geo>')
def get_location(geo):
	geo = geo.split(',')
	geo_lat = geo[0]
	geo_long = geo[1]
	location = Location()
	json = {}
	venues = location.get_venues(geo_lat, geo_long)
	output = []
	for chinese, display in venues:
		output.append({'display':display, 'chinese':chinese})
	cmd = "SELECT * FROM location"
	location_res = db.query_db(cmd)
	for venue in location_res:
		json_venue = {'display':venue[1], 'chinese':venue[2]}
		if json_venue['display'] not in map(lambda x: x['display'], output):
			output.append(json_venue)
	json['locations'] = output
	return flask.jsonify(json)

@app.route('/'+root+'/location/action/<venue>')
def get_action(venue):
	json = {}
	cmd = "SELECT id FROM location WHERE chinese_name = '%s'" \
			% (venue)
	location_id = db.query_db(cmd)[0][0]
	cmd = "SELECT a.chinese_name, a.english_name FROM action AS a, \
			location_action AS b WHERE b.location_id = %s AND \
			a.id = b.action_id" % (location_id)
	action_res = db.query_db(cmd)
	output = []
	output.append({'display':'anything', 'chinese':u'任何事'})
	for action in action_res:
		chinese, display = action
		output.append({'display':display, 'chinese':chinese})
	json['actions'] = output
	return flask.jsonify(json)

@app.route('/'+root+'/location/<venue>/<action>/concept/user/<user_id>')
def get_concept(venue, action, user_id):
	json = {}
	# display count upperbound
	cmd = "SELECT id FROM location WHERE chinese_name = '%s'" \
			% (venue)
	location_id = db.query_db(cmd)[0][0]
	# not only from location
	cmd = "SELECT concept_id FROM user_location_concept \
			WHERE user_id = %s AND location_id = %s" \
			% (user_id, location_id)
	concept_limit = len(db.query_db(cmd))
	if concept_limit == 0:
		concept_limit = 3
	elif concept_limit < 20:
		concept_limit += 3
	else:
		concept_limit = 20
	category_offset = 0
	categories = {}
	# find related concepts for location
	cmd = "SELECT a.id, a.name, b.category, a.difficulty FROM concept AS a, \
			location_concept AS b WHERE b.location_id = %s AND \
			a.id = b.concept_id ORDER BY a.difficulty" \
			% (location_id)
	concept_res = db.query_db(cmd)
	output = []
	from math import log
	concept_list = []
	for concept in concept_res:
		concept_id, chinese, category, difficulty = concept
		cmd = "SELECT view_count FROM user_concept WHERE user_id = %s \
				AND concept_id = %s" % (user_id, concept_id)
		res = db.query_db(cmd)
		if len(res) > 0:
			view_count = res[0][0]
		else:
			view_count = 0
		font_size = 50 - 3*int(view_count)
		if font_size <  30:
			continue
		concept_list.append(chinese)
		if len(concept_list) >= concept_limit:
			break
		category_key = venue+'|'+str(category)
		if category_key not in categories.keys():
			categories[category_key] = category_offset + 1
			category_offset += 1
		# calculate font size
		output.append({'chinese':chinese, \
						'category':categories[category_key], \
						'difficulty':difficulty, 'font_size':font_size})
	category_offset += len(categories)
	# find related concepts for action
	if action != u'任何事':
		cmd = "SELECT id FROM action WHERE chinese_name = '%s'" \
				% (action)
	else:
		cmd = "SELECT action_id FROM location_action WHERE location_id = %s" \
				% (location_id)
	for action_item in db.query_db(cmd):
		action_id = action_item[0]
		cmd = "SELECT a.id, a.name, b.category, a.difficulty FROM concept AS a, \
				action_concept AS b WHERE b.action_id = %s AND \
				a.id = b.concept_id ORDER BY a.difficulty" \
				% (action_id)
		concept_res = db.query_db(cmd)
		concept_list = []
		for concept in concept_res:
			concept_id, chinese, category, difficulty = concept
			cmd = "SELECT view_count FROM user_concept WHERE user_id = %s \
					AND concept_id = %s" % (user_id, concept_id)
			res = db.query_db(cmd)
			if len(res) > 0:
				view_count = res[0][0]
			else:
				view_count = 0
			font_size = 50 - 3*int(view_count)
			if font_size <  30:
				continue
			concept_list.append(chinese)
			if len(concept_list) >= concept_limit:
				break
			category_key = str(action_id)+'|'+str(category)
			if category_key not in categories.keys():
				categories[category_key] = category_offset + 1
				category_offset += 1
			if chinese not in map(lambda x: x['chinese'], output):
				output.append({'chinese':chinese, \
								'category':categories[category_key], \
								'difficulty':difficulty, 'font_size':font_size})
	# sort output by difficulty and relabel the category
	output = sorted(output, key=lambda item: item['difficulty'])
	category_offset = 0
	category_map = {}
	output_json = []
	for concept in output:
		if len(output_json) > concept_limit:
			break
		if category_offset >= 10:
			continue
		if concept['category'] not in category_map.keys():
			category_map[concept['category']] = category_offset
			category_offset += 1
		concept['category'] = category_map[concept['category']]
		output_json.append(concept)
	json['concepts'] = output_json
	return flask.jsonify(json)

@app.route('/'+root+'/concept/<concept>')
def get_concept_info(concept):
	json = {}
	cmd = "SELECT * FROM concept WHERE name = '%s'" % (concept)
	concept_res = db.query_db(cmd)
	concept = concept_res[0]
	output = []
	#TODO: We need to have intermediate certificate 
	#      to access audio from flask server.
	audio_file = \
			'http://lime.csie.ntu.edu.tw/~a33kuo/language-learner/audio/concept/' \
			+ str(concept[0]) + '.wav'
	if concept[5] != None and concept[5] != '':
		image_file = flask.url_for('static', \
				filename='img/concept/'+concept[5])
	else:
		image_file = 'None'
	output.append({'chinese':concept[1], 'image':image_file, \
					'pinyin':concept[6], 'audio':audio_file, \
					'english':concept[7]})
	json['concept'] = output
	return flask.jsonify(json)

@app.route('/'+root+'/concept/<concept>/dialog/<location>/<action>')
def get_concept_dialog(concept, location, action):
	json = {}
	cmd = "SELECT id, english FROM concept WHERE name = '%s'" % (concept)
	concept_res = db.query_db(cmd)
	concept_id = concept_res[0][0]
	concept_english = concept_res[0][1]
	cmd = "SELECT id FROM location WHERE chinese_name = '%s'" % (location)
	location_id = db.query_db(cmd)[0][0]
	cmd = "SELECT category FROM location_concept WHERE \
			location_id = %s AND concept_id = %s" % (location_id, concept_id)
	category_res = db.query_db(cmd)
	if len(category_res) != 0:
		category = category_res[0][0]
		cmd = "SELECT b.id, b.content FROM dialog_location_category AS a, \
				dialog AS b WHERE a.dialog_id = b.id AND \
				a.location_id = %s AND a.category = %s ORDER BY b.difficulty" \
				% (location_id, category)
		dialog_res = db.query_db(cmd)
		if len(dialog_res) > 0:
			dialog_id = dialog_res[0][0]
			dialog = dialog_res[0][1]
			matches = re.findall(r'\[\w+\]', \
					dialog, flags=re.UNICODE)
			matches = list(set(matches))
			for match in matches:
				match = match.replace('[', '').replace(']', '')
				cmd = "SELECT a.category, b.english FROM \
						location_concept AS a, concept AS b \
						WHERE a.location_id = %s AND b.name = '%s' AND \
						a.concept_id = b.id" % (location_id, match)
				category_res = db.query_db(cmd)
				if len(category_res) > 0:
					if category == category_res[0][0]:
						json['dialog_id'] = dialog_id
						json['dialog'] = []
						dialog = dialog.replace(category_res[0][1], concept_english)
						t = BingTranslate()
						for sentence in \
								dialog.replace(match, concept).split('\n'):
							chinese = sentence.split('\t')[0]
							english = sentence.split('\t')[1]
							cmd = "SELECT id FROM sentence WHERE sentence = '%s'" % (chinese)
							sentence_res = db.query_db(cmd)
							if len(sentence_res) == 0:
								cmd = "INSERT INTO sentence (sentence) VALUES ('%s')" % (chinese)
								db.query_db(cmd)
								cmd = "SELECT id FROM sentence WHERE sentence = '%s'" % (chinese)
								sentence_res = db.query_db(cmd)
								filename = '/home/a33kuo/public_html/language-learner/audio/dialog/'+str(sentence_res[0][0])+'.wav'
								t.get_speech(chinese.replace('[', '').replace(']', ''), filename, "zh-CHT")
							audio_file = 'http://lime.csie.ntu.edu.tw/~a33kuo/language-learner/audio/dialog/'+str(sentence_res[0][0])+'.wav'
							json['dialog'].append(\
									{'chinese':chinese, 'english':english, 'audio':audio_file})
						break
	return flask.jsonify(json)

@app.route('/'+root+'/login/<email>')
def login(email):
	json = {}
	cmd = "SELECT * FROM user WHERE email = '%s'" % (email)
	user_res = db.query_db(cmd)
	if len(user_res) <= 0:
		cmd = u"INSERT INTO user (email) VALUES ('%s')" % (email)
		db.query_db(cmd)
	cmd = "SELECT * FROM user WHERE email = '%s'" % (email)
	user_res = db.query_db(cmd)
	json['user'] = email.split('@')[0]
	json['user_id'] = user_res[0][0]
	return flask.jsonify(json)

@app.route('/'+root+'/user/<user_id>/concept/<concept>/view')
def update_user_view_count(user_id, concept):
	json = {}
	cmd = u"SELECT id FROM concept WHERE name = '%s'" % (concept)
	concept_id = db.query_db(cmd)[0][0]
	cmd = "SELECT * FROM user_concept WHERE user_id = %s AND concept_id = %s" \
			% (user_id, concept_id)
	user_res = db.query_db(cmd)
	if len(user_res) > 0:
		cmd = "UPDATE user_concept SET view_count = view_count + 1 \
				WHERE user_id = %s AND concept_id = %s" % (user_id, concept_id)
	else:
		cmd = "INSERT INTO user_concept (user_id, concept_id, view_count) \
				VALUES (%s, %s, 1)" % (user_id, concept_id)
	db.query_db(cmd)
	cmd = "SELECT view_count FROM user_concept WHERE user_id = %s AND concept_id = %s" \
			% (user_id, concept_id)
	view_count = db.query_db(cmd)[0][0]
	json['view_count'] = view_count
	return flask.jsonify(json)

@app.route('/'+root+'/user/<user_id>/location/<venue>/concept/<concept>/view')
def update_user_location_concept(user_id, venue, concept):
	json = {}
	cmd = u"SELECT id FROM concept WHERE name = '%s'" % (concept)
	concept_id = db.query_db(cmd)[0][0]
	cmd = u"SELECT id FROM location WHERE chinese_name = '%s'" % (venue)
	location_id = db.query_db(cmd)[0][0]
	cmd = "SELECT * FROM user_location_concept WHERE user_id = %s \
			AND location_id = %s AND concept_id = %s" \
			% (user_id, location_id, concept_id)
	user_res = db.query_db(cmd)
	if len(user_res) > 0:
		pass
	else:
		cmd = "INSERT INTO user_location_concept (user_id, location_id, concept_id) \
				VALUES (%s, %s, %s)" % (user_id, location_id, concept_id)
		db.query_db(cmd)
	json['location_id'] = location_id
	return flask.jsonify(json)

@app.route('/'+root+'/')
def index():
	return flask.render_template('index.html')

@app.route('/'+root+'/menu/')
def select_context():
	return flask.render_template('select-context.html')

@app.route('/'+root+'/learn/')
def overview():
	location = flask.request.args.get('location')
	return flask.render_template('overview.html')

@app.route('/'+root+'/learn/front/')
def learn_front():
	return flask.render_template('learn-front.html')

@app.route('/'+root+'/learn/back/')
def learn_back():
	return flask.render_template('learn-back.html')

@app.errorhandler(404)
def not_found(error):
	return flask.jsonify({'error':'invalid request'})


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')
