from flask import Flask, jsonify, request
import fetch
from threading import Thread

app = Flask(__name__)

db = {}

"""
[{
	__source_addr : readings,
	
}...]
"""

@app.route('/api/fetch/<int:num>', methods = ['GET'])
def grab(num):
	files = fetch.fetch(num)
	return jsonify({'files' : files})
	#run reset command to fetch new songs

@app.route('/api/clear/', methods = ['GET'])
def clear():
	print "clear"
	#Clear current cache of songs

app.run(host='0.0.0.0', port=8000, debug=True)
