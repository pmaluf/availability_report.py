#!/usr/bin/python
#
# availability_report.py - Sensu Availability Report
# Criacao: Paulo Victor Maluf Alves - 01/2018
#
# Changelog:
#
# Date       Author              Description
# ---------- ------------------- ---------------------------------------------
# ============================================================================
import pandas as pd
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from argparse import ArgumentParser
import urllib2
import base64
import json

# Global Variables
SENSU_URL = "http://sensu-server:4567"
SENSU_AUTH = True
SENSU_USER = "sensu"
SENSU_PASS = "sensupasswd"
matrix = []
alarm = {}


def sensu(api):
    url = "{}/{}".format(SENSU_URL, api)

    if SENSU_AUTH:
        request = urllib2.Request(url)
        base64string = base64.encodestring('{}:{}'.format(SENSU_USER,
                                                          SENSU_PASS))
        base64string = base64string.replace('\n', '')
        request.add_header("Authorization", "Basic {}".
                           format(base64string))
        result = urllib2.urlopen(request)
    else:
        result = urllib2.urlopen(url)

    json_decoded = json.loads(result.read(), encoding='latin1')
    return json_decoded


def get_logstash_index(start_date='foo', end_date='bar'):
    index = ''
    if start_date == 'foo':
        now = datetime.now()
        index = 'logstash-{}.{:02d}.*'.format(now.year, now.month)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        delta = end_date - start_date
        for i in range(delta.days + 1):
            delta = start_date + timedelta(days=i)
            index += 'logstash-{:%Y.%m.%d},'.format(delta)
        index = index[:-1]

    return index


def unix_time_millis(datetime):
    epoch = datetime.utcfromtimestamp(0)
    return (datetime-epoch).total_seconds()


def elastic_search(host, port, index):
    try:
        es = Elasticsearch([{'host': host, 'port': port}],
                           timeout=300)
    except Exception as err:
        print "Connection error:", err

    rs = es.search(
        index=index,
        scroll="2m",
        body={
           "size": 10000,
           "query": {
              "bool": {
                 "must": [
                    {
                       "query_string": {
                          "query": "_type:\"sensu-logstash\""
                       }
                    }
                 ],
              }
           },
           "aggs": {
              "max_timestamp": {
                 "max": {
                    "field": "@timestamp"
                 }
              },
              "min_timestamp": {
                 "min": {
                    "field": "@timestamp"
                 }
              }
           },
           "sort": [
              {
                 "@timestamp": {
                    "order": "asc"
                 }
              }
           ]
        })
    return rs


def elastic_scroll(host, port, scroll_id):
    try:
        es = Elasticsearch([{'host': host, 'port': port}],
                           timeout=300)
    except Exception as err:
        print "Connection error:", err

    rs = es.scroll(scroll_id=scroll_id, scroll='2m')
    return rs


def validate_date_format(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


def main():
    parser = ArgumentParser()
    parser.add_argument('-H', '--elastic-host', action='store',
                        dest='host', default='elk.domain.infra',
                        help='The elasticsearch you want to connect to')
    parser.add_argument('-P', '--port', action='store', dest='port',
                        default=9200,
                        help='The port elasticsearch is running on')
    parser.add_argument('-s', '--start-date', action='store',
                        dest='start_date',
                        help='The start date of report. (YYYY-MM-DD)')
    parser.add_argument('-e', '--end-date', action='store', dest='end_date',
                        help='The end time of report. (YYYY-MM-DD)')
    parser.add_argument('-c', '--csv', action='store_true', dest='csv',
                        help='Output in csv format')
    args = parser.parse_args()

    if args.start_date and args.end_date is None:
        parser.error("--start-date requires --end-date.")
    elif args.end_date and args.start_date is None:
        parser.error("--end-date requires --start-date.")

    if args.start_date:
        validate_date_format(args.start_date)
        validate_date_format(args.end_date)
        logstash_index = get_logstash_index(args.start_date, args.end_date)
    else:
        logstash_index = get_logstash_index()

    rs = elastic_search(args.host, args.port, logstash_index)

    scroll_id = rs['_scroll_id']
    scroll_size = rs['hits']['total']

    min_timestamp = rs['aggregations']['min_timestamp']['value']/1000
    max_timestamp = rs['aggregations']['max_timestamp']['value']/1000
    totaltime = max_timestamp-min_timestamp

    while scroll_size > 0:
        for hit in rs['hits']['hits']:
            current_timestamp = hit['_source']['@timestamp']
            unique_id = hit['_source']['unique_id'].upper()
            status = hit['_source']['status'].upper()
            tags = hit['_source']['tags'][0].upper()

            dt = datetime.strptime(current_timestamp,
                                   "%Y-%m-%dT%H:%M:%S.%fZ")

            timestamp = unix_time_millis(dt)

            if (status == 'CRITICAL' or status == 'UNKNOWN' or
               status == 'WARNING'):
                # alarm { 'unique_id': { timestamp: 123456, status: 'OK' }}
                alarm[unique_id] = {'status': status, 'timestamp': timestamp}

            if tags == 'SENSU-RESOLVE':
                if unique_id in alarm:
                    if (alarm[unique_id]['status'] == 'CRITICAL' or
                            alarm[unique_id]['status'] == 'UNKNOWN'):
                        downtime = timestamp-alarm[unique_id]['timestamp']
                        del alarm[unique_id]
                        matrix.append([unique_id, int(downtime)])
                    elif alarm[unique_id]['status'] == 'WARNING':
                        del alarm[unique_id]
                else:
                    downtime = timestamp-min_timestamp
                    matrix.append([unique_id, int(downtime)])

        rs = elastic_scroll(args.host, args.port, scroll_id)
        scroll_id = rs['_scroll_id']
        scroll_size = len(rs['hits']['hits'])
        # print scroll_size

    data = pd.DataFrame.from_dict(matrix)

    mytab = data.groupby([0]).agg({0: 'count', 1: sum})
    mytab = mytab.reindex(mytab.index.rename('Check_name'))
    mytab = mytab.rename(columns={0: "Alarms",
                                  1: "Downtime", 2: "Availability"})

    mytab['Availability'] = ((totaltime-(mytab['Downtime']))/totaltime)*100

    # Get all checks count
    total_checks = sensu('results/sensu-server/Check_qtd_checks')
    total_checks = int(total_checks['check']['output'])

    availability_median = mytab['Availability'].median()

    # total_alarms = mytab['Alarms'].nunique()

    total_alarms = mytab['Alarms'].count()

    # total_downtime = ((totaltime-(mytab['Downtime'].sum()))/totaltime)*100
    infra_availability = (((total_checks-total_alarms)*100) +
                          (total_alarms * availability_median)) / total_checks

    if args.csv:
        print mytab.to_csv()
        # print "\nTotal Downtime in period: {:f}".format(total_downtime)
        print "Infrastruture Availability,,,{:f}".format(infra_availability)
    else:
        print mytab.to_string()
        # print "\nTotal Downtime in period: {:f}".format(total_downtime)
        print "Infrastruture Availability: {:f}".format(infra_availability)


if __name__ == "__main__":
    main()
