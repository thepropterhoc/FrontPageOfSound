from flask import Flask, jsonify, request
from threading import Thread

app = Flask(__name__)

db = {}

"""
[{
	__source_addr : readings,
	
}...]
"""

@app.route('/api/xbee/<string:val_id>/channel/<int:channel_id>', methods = ['GET'])
def get_val(self, val_id):
	val = filter(lambda x: x['channel'] == val_id, list(vals))[0]
	return jsonify(self.val)

@app.route('/api/all/', methods = ['GET'])
def get_all():
	return jsonify({'db' : db})

@app.route('/api/alerts/', methods = ['GET'])
def get_alerts(self):
	print alerts
	return jsonify({'alerts' : alerts})
	
@app.route('/api/update', methods = ['POST'])
def update():
	frame = request.json
	db[frame['source_addr_long']] = frame['samples']
	print db
	return jsonify({})

app.run(host='0.0.0.0', port=80, debug=True)
