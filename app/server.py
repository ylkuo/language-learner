# -*- coding: utf-8 -*-

import flask
import os, sys
import simplejson
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
		if json_venue not in output:
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

@app.route('/'+root+'/location/<venue>/concept')
def get_concept(venue):
	json = {}
	cmd = "SELECT id FROM location WHERE chinese_name = '%s'" \
			% (venue)
	location_id = db.query_db(cmd)[0][0]
	cmd = "SELECT a.name, b.category, a.difficulty FROM concept AS a, \
			location_concept AS b WHERE b.location_id = %s AND \
			a.id = b.concept_id ORDER BY a.difficulty" % (location_id)
	concept_res = db.query_db(cmd)
	output = []
	for concept in concept_res:
		chinese, category, difficulty = concept
		output.append({'chinese':chinese, 'category':category, \
						'difficulty':difficulty})
	json['concepts'] = output
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
					'pinyin':concept[6], 'audio':audio_file})
	json['concept'] = output
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
