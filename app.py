"""The main application logic."""
from flask import Flask
from flask import jsonify, render_template
from json_response import json_success
from google.transit import gtfs_realtime_pb2
from datetime import datetime
import urllib2
from protobuf_to_dict import protobuf_to_dict
import threading
from time import sleep


# Flask
app = Flask(__name__,
            static_folder='static/dist/',
            static_url_path='/static')
app.config.from_object('config.flask_config')

# MTA API url
MTA_URL = 'http://datamine.mta.info/mta_esi.php?feed=1&key={}'.format(
    app.config['MTA_KEY'])
UPTOWN_STOP_ID = '116N'
DOWNTOWN_STOP_ID = '116S'

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


def _convert_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp)


def _convert_timestamps(entities):
    global mta_data
    for entity in entities:
        if 'trip_update' in entity:
            for update in entity['trip_update']['stop_time_update']:
                for key in ('arrival', 'departure'):
                    if key in update:
                        update[key]['time'] = _convert_timestamp(
                            update[key]['time'])
        if 'vehicle' in entity:
            entity['vehicle']['timestamp'] = _convert_timestamp(
                entity['vehicle']['timestamp'])


def _minutes_until(dt):
    if not dt:
        return 0

    return int((dt - datetime.now()).seconds / 60)


def _check_update(update, direction, stop_id):
    if (update['stop_id'] != stop_id or 'departure' not in update):
        return

    candidate = update['departure']['time']

    if (not best[direction] or
            best[direction] < datetime.now() or
            (candidate < best[direction] and candidate > datetime.now())):
        best[direction] = candidate
        estimates[direction] = _minutes_until(candidate)


def _compute_estimates(entities):
    for entity in entities:
        if 'trip_update' not in entity:
            continue

        for update in entity.get('trip_update').get('stop_time_update'):
            _check_update(update, 'uptown', UPTOWN_STOP_ID)
            _check_update(update, 'downtown', DOWNTOWN_STOP_ID)


def _recompute_estimates():
    estimates['uptown'] = _minutes_until(best['uptown'])
    estimates['downtown'] = _minutes_until(best['downtown'])


def poll_mta():
    """Poll MTA for new mta_data every five seconds."""
    global mta_data
    while True:
        feed = gtfs_realtime_pb2.FeedMessage()
        response = urllib2.urlopen(MTA_URL)
        feed.ParseFromString(response.read())
        mta_data = protobuf_to_dict(feed)
        _convert_timestamps(mta_data['entity'])
        _compute_estimates(mta_data['entity'])
        sleep(5)

# Start polling the MTA
t = threading.Thread(target=poll_mta)
t.setDaemon(True)
t.start()


@app.route('/')
def index():
    """"Index route."""
    _recompute_estimates()
    return render_template('index.html', estimates=estimates)


@app.route('/data')
def data():
    """"Show all of our MTA data as JSON."""
    return jsonify(mta_data)


@app.route('/estimates')
def get_estimates():
    """Show just our estimates as JSON."""
    _recompute_estimates()
    return json_success(estimates)

if __name__ == '__main__':
    app.run()
