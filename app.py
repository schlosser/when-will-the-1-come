"""The main application logic."""
from flask import Flask
from flask import jsonify, render_template
from json_response import json_success
from google.transit import gtfs_realtime_pb2
import urllib2
from protobuf_to_dict import protobuf_to_dict
import threading
from time import sleep
from clean import *


# Flask
app = Flask(__name__,
            static_folder='static/dist/',
            static_url_path='/static')
app.config.from_object('config.flask_config')

# MTA API url
MTA_URL = 'http://datamine.mta.info/mta_esi.php?feed=1&key={}'.format(
    app.config['MTA_KEY'])

# State
mta_data = {}
best = {
    'uptown': None,
    'downtown': None
}
estimates = {
    'uptown': 0,
    'downtown': 0
}


def poll_mta():
    """Poll MTA for new mta_data every five seconds."""
    global mta_data, best, estimates
    latest_timestamp = -1
    while True:
        feed = gtfs_realtime_pb2.FeedMessage()
        response = urllib2.urlopen(MTA_URL)
        feed.ParseFromString(response.read())
        dict_data = protobuf_to_dict(feed)
        if dict_data['header']['timestamp'] != latest_timestamp:
            latest_timestamp = dict_data['header']['timestamp']
            print 'UPDATE @ timestamp:', latest_timestamp
            mta_data = filter_data(dict_data)
            convert_timestamps(mta_data['entity'])
            best, estimates = compute_estimates(mta_data['entity'],
                                                best,
                                                estimates)
            if app.config['STDOUT']:
                print mta_data
        sleep(5)

# Start polling the MTA
t = threading.Thread(target=poll_mta)
t.setDaemon(True)
t.start()


@app.route('/')
def index():
    """"Index route."""
    return render_template('index.html', estimates=estimates)


@app.route('/data')
def data():
    """"Show all of our MTA data as JSON."""
    return jsonify(mta_data)


def _best_to_string(best):
    return dict((k, str(v)) for k, v in best.iteritems())


@app.route('/estimates')
def get_estimates():
    """Show just our estimates as JSON."""
    return json_success({
        'estimates': estimates,
        'best': _best_to_string(best),
    })

if __name__ == '__main__':
    if app.config['STDOUT']:
        print "Press Ctrl + C to quit."
        while True:  # infinite loop, while the thread prints
            pass
    else:
        app.run()
