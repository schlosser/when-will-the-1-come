from datetime import datetime

UPTOWN_STOP_ID = '116N'
DOWNTOWN_STOP_ID = '116S'


def _convert_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp)


def convert_timestamps(entities):
    """Convert timestamps to datetimes."""
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


def _check_update(update, direction, stop_id, best, estimates):
    if (update['stop_id'] != stop_id or 'departure' not in update):
        return best, estimates

    candidate = update['departure']['time']

    if (not best[direction] or
            best[direction] < datetime.now() or
            (candidate < best[direction] and candidate > datetime.now())):
        best[direction] = candidate
        estimates[direction] = _minutes_until(candidate)

    return best, estimates


def compute_estimates(entities, best, estimates):
    """Compute final estimates from the data."""
    for entity in entities:
        if 'trip_update' not in entity:
            continue

        for update in entity.get('trip_update').get('stop_time_update'):
            best, estimates = _check_update(
                update, 'uptown', UPTOWN_STOP_ID, best, estimates)
            best, estimates = _check_update(
                update, 'downtown', DOWNTOWN_STOP_ID, best, estimates)

    return best, estimates


def filter_data(dict_data):
    """Filter out bad data."""
    def _true_if_nontrivial_update(update):
        return bool(update['trip_update']['stop_time_update'])

    return {
        'entity': filter(_true_if_nontrivial_update, [
            {
                'id': entity['id'],
                'trip_update': {
                    'stop_time_update': [
                        update
                        for update in entity['trip_update']['stop_time_update']
                        if update['stop_id'].startswith('116')
                    ],
                    'trip': entity['trip_update']['trip']
                }
            }
            for entity in dict_data['entity']
            if (entity.get('trip_update') and
                entity['trip_update']['trip']['route_id'] == '1')
        ]),
        'header': dict_data['header']
    }
