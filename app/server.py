# -*- coding: utf-8 -*-

import flask
import os, sys
import simplejson
from context import Location

app = flask.Flask(__name__)

if len(sys.argv) == 1:
    root = 'language-learner'
else:
    root = sys.argv[1]

app_path = os.path.abspath(__file__).replace(\
		os.path.basename(__file__), '').replace(\
		os.path.abspath(__file__).split('/')[-2]+'/', 'app/')

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
	json['locations'] = output
	return flask.jsonify(json)

@app.route('/'+root+'/')
def select_context():
	return flask.render_template('select-context.html')

@app.route('/'+root+'/learn/')
def test():
	location = flask.request.args.get('location')
	return flask.render_template('test.html')

@app.errorhandler(404)
def not_found(error):
	return flask.jsonify({'error':'invalid request'})


if __name__ == "__main__":
	app.run(host='0.0.0.0')
