"""
Disclaimer
These projects are not a part of Datadog's subscription services and are provided for example purposes only.
They are NOT guaranteed to be bug free and are not production quality.
If you choose to use to adapt them for use in a production environment, you do so at your own risk.
"""

import json
import os
import pdb
import random
import time

from argparse import ArgumentParser
from datadog import initialize, api

DD_API_KEY = os.getenv('DD_API_KEY', '')
DD_APP_KEY = os.getenv('DD_APP_KEY', '')

options = {
    'api_key': DD_API_KEY,
    'app_key': DD_APP_KEY
}

ACCELERATED_INSTANCE_TYPES = ['p2', 'p3', 'g2', 'g3', 'g4', 'f1', 'inf1']

initialize(**options)

def is_complete_series(pointlist):
    if len(pointlist) < NUM_POINTS:
        return False
    for p in pointlist:
        if p[1] is None:
            return False
    return True

def is_not_accelerated(tag_set):
    for tag in tag_set:
        split_tag = tag.split(':')
        if split_tag[0] == 'instance-type':
            instance_type = split_tag[1].split('.')[0]
            if instance_type in ACCELERATED_INSTANCE_TYPES:
                print(instance_type)
                return False
    return True

def get_underutilized_tag_set(series, threshold, opt):
    under_tags = []
    total = 0
    hosts_under = 0
    for s in series:
        total += 1
        under = False
        tags = []
        val = None
        pointlist = s['pointlist']
        tag_set = s['tag_set']
        if is_complete_series(pointlist) and is_not_accelerated(tag_set):
            try:
                val = max([p[1] for p in pointlist])
                if (opt == 'less_than' and val < threshold) or (opt == 'greater_than' and val > threshold):
                    hosts_under += 1
                    under = True
                if under:
                    for t in tag_set:
                        if 'N/A' in t or len(t) == 0:
                            pass
                        else:
                            tags.append(t)
                    tags.sort()
                    tags_string = ','.join(tags)
                    under_tags.append(tags_string)
            except:
                print('------ Exception parsing series ------')
                print(s)
                continue
    print('total: %s' % total)
    print('hosts_under: %s' % hosts_under)
    return under_tags

def tags_to_dict(tags):
    tags_dict = {}
    for t in tags:
        if t in tags_dict:
            v = tags_dict[t] + 1
            tags_dict[t] = v
        else:
            tags_dict[t] = 1
    return tags_dict

def gen_metrics_from_tags_dict(tags_dict, metric_name):
    metrics = []
    for k, v in tags_dict.items():
        tags = k.split(',')
        value = v
        metrics.append({'name': metric_name, 'value': value, 'tags': tags})
    return metrics

def get_timeseries(query, seconds):
    now = int(time.time())
    res = api.Metric.query(start=now - seconds, end=now, query=query)
    if res['status'] == 'ok':
        return res['series']
    else:
        print(res['status'], res['error'])
        return []

def load_json_file(filename):
    with open(filename) as infile:
        data = json.load(infile)
    return data

def build_query(metric, agg, scope, tags, rollup):
    query = '%s:%s{%s} by {host, instance-type%s}.rollup(%s, %s)' % (agg, metric, scope, tags, agg, str(rollup))
    return query


if __name__ == "__main__":

    parser = ArgumentParser(description='Create EC2 pricing metrics from AWS Prices')
    parser.add_argument('-i', help='Input Settings File', required=True)
    parser.add_argument('-o', help='Output Metrics File', required=True)

    args = parser.parse_args()

    infile = args.i if args.i else 'metric_config.json'
    outfile = args.o if args.o else 'util_metrics.json'

    # Defaults
    START_SECONDS, QUERY_ROLLUP, SCOPE, TAGS = 86400, 3600, '*', ''

    try:
        settings = load_json_file(infile)
        QUERY_ROLLUP = settings['QUERY_ROLLUP']
        START_SECONDS = settings['MIN_TIME_UNDERUTILIZED'] + QUERY_ROLLUP
        SCOPE = settings['SCOPE']
        TAGS = settings['TAGS']
        METRICS = settings['METRICS']
        DD_COMBINED_METRIC = settings['DD_COMBINED_METRIC']
    except Exception as e:
        print(e)
        exit()


    TAGS = ', ' + TAGS if TAGS else ''
    NUM_POINTS = START_SECONDS / QUERY_ROLLUP - 2
    UTIL_METRICS = []
    for metric in METRICS:
        query = build_query(metric['metric'], metric['aggregation'], SCOPE, TAGS, QUERY_ROLLUP)
        series = get_timeseries(query, START_SECONDS)
        tagset = get_underutilized_tag_set(series, metric['threshold'], metric['operator'])
        tag_dict = tags_to_dict(tagset)
        metrics = gen_metrics_from_tags_dict(tag_dict, metric['custom_metric'])
        UTIL_METRICS.append({"metrics":metrics, "tagset": tagset})

    # Everything below assumes only two metrics in settings.
    # TODO: account for additional metrics
    combined_tagset = [ts for ts in UTIL_METRICS[0]['tagset'] if ts in UTIL_METRICS[1]['tagset']]
    combined_tag_dict = tags_to_dict(combined_tagset)
    combined_metrics = gen_metrics_from_tags_dict(combined_tag_dict, DD_COMBINED_METRIC)

    print('combined: %s' % len(combined_tagset))

    all_metrics = UTIL_METRICS[0]['metrics'] + UTIL_METRICS[1]['metrics'] + combined_metrics

    with open(outfile, 'wt') as out:
        json.dump(all_metrics, out, sort_keys=True, indent=4, separators=(',', ': '))
