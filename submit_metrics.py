"""
Disclaimer
These projects are not a part of Datadog's subscription services and are provided for example purposes only.
They are NOT guaranteed to be bug free and are not production quality.
If you choose to use to adapt them for use in a production environment, you do so at your own risk.
"""

import json

from datadog import statsd

files = ['custom_metrics.json', 'pricing_metrics.json']

for file in files:
    cnt = 0
    try:
        with open(file) as json_file:
            metrics = json.load(json_file)
            for metric in metrics:
                statsd.gauge(metric['name'], metric['value'], tags=metric['tags'])
                cnt += 1
    except Exception as e:
        print(e)
    print('ok - %s - %s' % (file, cnt))
