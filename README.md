1. Customize `metric_config.json` to adjust any metric names or thresholds.  You will likely need to edit the TAGS field or possibly SCOPE. Leave the other settings as default to start.  Verify the TAG, SCOPE, and metric names by building the query in a timeseries widget first.

2. Either set environment variables for DD_API_KEY and DD_APP_KEY or set in `generate_custom_metrics.py`.

3. Test the generate metrics script to make sure everything is working and all dependencies are installed:

```
python /path/to/<REPO_NAME>/custom_metrics/generate_custom_metrics.py -i /path/to/<REPO_NAME>/custom_metrics/metric_config.json -o /path/to/<REPO_NAME>/custom_metrics/custom_metrics.json
```

4. Configure a cronjob to submit metrics every minute for contiguous visualization and monitoring

```
* * * * * /usr/bin/python /path/to/<REPO_NAME>/custom_metrics/submit_metrics.py >> metric_submit.log
```

Configure a cronjob to generate new metrics every 10 minutes beginning at the 5th minute to ensure all rollup data points have a value.  `generate_custom_metrics` takes 2 args:

-i the input file, generally metric_config.json
-o the output file to be read by `submit_metrics.py`.  recommended `/path/to/<REPO_NAME>/custom_metrics/custom_metrics.json`.

```
5-59/10 * * * * /usr/bin/python /path/to/<REPO_NAME>/custom_metrics/generate_custom_metrics.py -i /path/to/<REPO_NAME>/custom_metrics/metric_config.json -o /path/to/<REPO_NAME>/custom_metrics/custom_metrics.json >> gen_metrics.log
```
