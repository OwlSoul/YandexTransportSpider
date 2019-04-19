#!/usr/bin/env python3

__author__ = "Yury D."
__credits__ = ["Yury D."]
__license__ = "MIT"
__version__ = "0.0.2"
__maintainer__ = "Yury D."
__email__ = "TheOwlSoul@gmail.com"
__status__ = "Alpha"

import psycopg2
import sys
import time
import argparse
import os

database_settings = {
    'db_name': 'yandex_transport',
    'db_user': 'yandex_transport',
    'db_host': 'localhost',
    'db_port': 5432,
    'db_password': 'password'
}

delay_time = 60


def get_queue(db_settings):
    try:
        conn = psycopg2.connect("dbname='" + db_settings['db_name'] + "'" +
                                "user='" + db_settings['db_user'] + "'" +
                                "host='" + db_settings['db_host'] + "'" +
                                "password='" + db_settings['db_password'] + "'")
    except Exception as e:
        print("Exception (connect to database):" + str(e))
        sys.exit(1)

    result = None
    sql_query = "SELECT id, type, data_id, thread_id FROM queue LIMIT 10"
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        result = cur.fetchall()
    except Exception as e:
        print("Exception (get queue, list):" + str(e))

    sql_query = "SELECT count(*) FROM (SELECT id FROM queue WHERE type='stop') AS sq1"
    try:
        cur.execute(sql_query)
        result_stops = cur.fetchall()
    except Exception as e:
        print("Exception (get queue, number of stops):" + str(e))

    sql_query = "SELECT count(*) FROM (SELECT id FROM queue WHERE type='route') AS sq1"
    try:
        cur.execute(sql_query)
        result_routes = cur.fetchall()
    except Exception as e:
        print("Exception (get queue, number of routes):" + str(e))

    conn.close()

    return result, result_stops[0][0], result_routes[0][0]

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Show current queue from database. Helper utility script.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-v", "--version", action="store_true", default=False,
                        help="show version info")
    parser.add_argument("--route_beep", action="store_true", default=False,
                        help="beep if route encountered")
    parser.add_argument("--database", metavar="DB_NAME", default=database_settings['db_name'],
                        help="Database name, default is " + database_settings['db_name'])
    parser.add_argument("--db_host", metavar="DB_HOST", default=database_settings['db_host'],
                        help="Database host, default is " + database_settings['db_host'])
    parser.add_argument("--db_port", metavar="DB_PORT", default=database_settings['db_port'],
                        help="Database port, default is " + str(database_settings['db_port']))
    parser.add_argument("--db_user", metavar="DB_USER", default=database_settings['db_user'],
                        help="Database username, default is " + database_settings['db_user'])
    parser.add_argument("--db_password", metavar="PASS", default=database_settings['db_password'],
                        help="Database password, default is " + database_settings['db_password'])
    parser.add_argument("--delay", metavar="DELAY", default=delay_time,
                        help="Delay between queries, default is " + str(delay_time))

    args = parser.parse_args()
    if args.version:
        print(__version__)
        sys.exit(0)

    database_settings["db_name"] = args.database
    database_settings["db_host"] = args.db_host
    database_settings["db_port"] = int(args.db_port)
    database_settings["db_user"] = args.db_user
    database_settings["db_password"] = args.db_password

    route_beep = args.route_beep

    delay_time = int(args.delay)

    while True:
        queue, stops_cnt, routes_cnt = get_queue(database_settings)
        do_beep = False
        for i, line in enumerate(queue):
            print(i, ":", line)
            if line[1]=='route':
                do_beep = True
        print("Total stops in queue  :", stops_cnt)
        print("Total routes in queue :", routes_cnt)
        print("")
        if do_beep:
            duration = 0.2  # seconds
            freq = 440  # Hz
            os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
        time.sleep(delay_time)