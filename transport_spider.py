#!/usr/bin/env python3

__author__ = "Yury D."
__credits__ = ["Yury D."]
__license__ = "MIT"
__version__ = "0.0.9"
__maintainer__ = "Yury D."
__email__ = "TheOwlSoul@gmail.com"
__status__ = "Alpha"

import json
import argparse
import psycopg2
from route_parser import parse_route
from stop_parser import parse_stop
import signal
import time
import sys
import random

class Application:
    def __init__(self):
        # "Is application running" flag
        self.is_running = True

        # Retry limit and wait time
        self.retry_limit = 5
        self.retry_sleep = 60

        # Database settings
        self.database_settings = {
            'db_name': 'yandex_transport',
            'db_user': 'yandex_transport',
            'db_host': 'localhost',
            'db_port': 5432,
            'db_password': 'password'
        }

        #Yandex Transport Proxy settings
        self.ytproxy_host = '127.0.0.1'
        self.ytproxy_port = 25555

        # Starting stop ID
        self.start_id = None

        # Delay tresholds, script will wait random time in range of these two between queries
        self.delay_lower = 40
        self.delay_upper = 60

        signal.signal(signal.SIGINT, self.sigint_handler)

    def get_record_from_queue(self, db_settings):
        try:
            conn = psycopg2.connect(dbname=db_settings['db_name'],
                                    host=db_settings['db_host'],
                                    user=db_settings['db_user'],
                                    port=db_settings['db_port'],
                                    password=db_settings['db_password'])
        except Exception as e:
            print("Exception (connect to database in get_record_from_queue):" + str(e))
            conn.close()
            return (None, None, None)

        sql_query = "SELECT type, data_id, thread_id FROM queue LIMIT 1"
        rows = []
        try:
            cur = conn.cursor()
            cur.execute(sql_query)
            rows = cur.fetchall()
        except Exception as e:
            print("Exception (get queue item):" + str(e))
            pass

        cur.close()
        conn.close()

        if not rows:
            return (None, None, None)
        else:
            return rows[0]


    def delete_from_queue(self, db_settings, type, data_id):
        try:
            conn = psycopg2.connect(dbname=db_settings['db_name'],
                                    host=db_settings['db_host'],
                                    user=db_settings['db_user'],
                                    port=db_settings['db_port'],
                                    password=db_settings['db_password'])
        except Exception as e:
            print("Exception (connect to database in delete_from_queue):" + str(e))
            conn.close()
            sys.exit(1)

        sql_query = "DELETE FROM queue WHERE type='" + type + "' AND data_id='" + data_id + "'"
        try:
            cur = conn.cursor()
            cur.execute(sql_query)
            conn.commit()
        except Exception as e:
            print("Exception (delete queue item):" + str(e))
            pass

    def get_queue_size(self, db_settings):
        try:
            conn = psycopg2.connect(dbname=db_settings['db_name'],
                                    host=db_settings['db_host'],
                                    user=db_settings['db_user'],
                                    port=db_settings['db_port'],
                                    password=db_settings['db_password'])
        except Exception as e:
            print("Exception (connect to database in get_queue_size):" + str(e))
            conn.close()
            sys.exit(1)

        result = None
        sql_query = "SELECT COUNT(*) FROM queue"
        try:
            cur = conn.cursor()
            cur.execute(sql_query)
            result = cur.fetchall()[0]
            conn.commit()
        except Exception as e:
            print("Exception (delete queue item in get_queue_size):" + str(e))
            pass
        return result

    def sigint_handler(self, sig, _):
        """
        SIGINT handler function
        :param sig: signal
        :param _: frame
        :return: nothing
        """
        print("Signal received:", sig)
        self.is_running = False

    def parse_args(self):
        parser = argparse.ArgumentParser(description="\U0001F577  Yandex Transport Spider \U0001F577 \n\n"
                                                     "You give it starting stop id and it \n"
                                                     "will crawl as far as it can go, checking all neighbouring stops \n"
                                                     "and routes, going through them and repeating until all stops \n"
                                                     "are exhausted.\n\n"
                                                     "Requires a PostgreSQL database with prepared database to work. \n"
                                                     "Can be stopped and resumed later.\n\n"
                                                     "It takes A LOT of time to crawl everything for big cities, \n"
                                                     "think about DAYS or even WEEKS with default timeout (1 minute).\n\n"
                                                     "Also requires running Yandex Transport Proxy.",
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("-v", "--version", action="store_true", default=False,
                            help="show version info")
        parser.add_argument("stop_id", default="", nargs='?',
                            help="Starting stop ID")
        parser.add_argument("--ytproxy_host", metavar="HOST", default=self.ytproxy_host,
                            help="Yandex Transport Proxy host, default is " + self.ytproxy_host)
        parser.add_argument("--ytproxy_port", metavar="PORT", default=self.ytproxy_port,
                            help="Yandex Transport Proxy port, default is " + str(self.ytproxy_port))
        parser.add_argument("--database", metavar="DB_NAME", default=self.database_settings['db_name'],
                            help="Database name, default is "+ self.database_settings['db_name'])
        parser.add_argument("--db_host", metavar="DB_HOST", default=self.database_settings['db_host'],
                            help="Database host, default is " + self.database_settings['db_host'])
        parser.add_argument("--db_port", metavar="DB_PORT", default=self.database_settings['db_port'],
                            help="Database port, default is " + str(self.database_settings['db_port']))
        parser.add_argument("--db_user", metavar="DB_USER", default=self.database_settings['db_user'],
                            help="Database username, default is " + self.database_settings['db_user'])
        parser.add_argument("--db_password", metavar="PASS", default=self.database_settings['db_password'],
                            help="Database password, default is " + self.database_settings['db_password'])
        parser.add_argument("--delay_lower", metavar="D_LOW", default=self.delay_lower,
                            help="Lower threshold of delay, default is " + str(self.delay_lower))
        parser.add_argument("--delay_upper", metavar="D_UP", default=self.delay_upper,
                            help="Upper threshold of delay, default is " + str(self.delay_upper))

        args = parser.parse_args()
        if args.version:
            print(__version__)
            sys.exit(0)

        if args.stop_id == "":
            print("No starting stop ID provided!")
            sys.exit(1)

        self.ytproxy_host = args.ytproxy_host
        self.ytproxy_port = int(args.ytproxy_port)

        self.database_settings["db_name"] = args.database
        self.database_settings["db_host"] = args.db_host
        self.database_settings["db_port"] = int(args.db_port)
        self.database_settings["db_user"] = args.db_user
        self.database_settings["db_password"] = args.db_password

        self.delay_lower = int(args.delay_lower)
        self.delay_upper = int(args.delay_upper)

        self.start_id = str(args.stop_id)

    def run(self, db_settings):
        self.parse_args()

        print("SPIDER STARTED")

        res = parse_stop(self.start_id, db_settings, self.ytproxy_host, self.ytproxy_port)
        if res == 1:
            sys.exit(1)

        if res != 2:
            wait_time = random.randint(self.delay_lower, self.delay_upper)
            for i in range(0, wait_time):
                if self.is_running:
                    time.sleep(1)

        # Counter for retry in case of Exception
        retry_counter = 0

        while self.is_running:

            query_type, query_data_id, query_thread_id = self.get_record_from_queue(db_settings)
            print("Type:", query_type, ";", "ID:", query_data_id)
            if query_data_id is None:
                print("query_data_id is None, I'll stop here.")
                sys.exit(0)

            if query_type == 'stop':
                res = parse_stop(query_data_id, db_settings, self.ytproxy_host, self.ytproxy_port)
            elif query_type == 'route':
                res = parse_route(query_data_id, query_thread_id, db_settings, self.ytproxy_host, self.ytproxy_port)

            if res == 1:
                retry_counter += 1
                if retry_counter > self.retry_limit:
                    print("There is a problem with getting data from the server, aborting spider for now")
                else:
                    print("Failed to get data, spider will chillax and relax for " +
                          str(self.retry_limit) +
                          " seconds now, bro.")
                    for i in range(0, self.retry_sleep):
                        if self.is_running:
                            time.sleep(1)

            else:
                retry_counter = 0

            self.delete_from_queue(db_settings, query_type, query_data_id)
            try:
                print("Objects in queue:", str(self.get_queue_size(db_settings)[0]))
            except:
                pass
            if res != 2:
                wait_time = random.randint(self.delay_lower, self.delay_upper)
            else:
                wait_time = 1
            print("Waiting " + str(wait_time) + " secs.")
            print("---------------------------------------------------------------------------------------------------")
            print("")
            for i in range(0, wait_time):
                if self.is_running:
                    time.sleep(1)

        print("SPIDER TERMINATED")

if __name__=='__main__':
    app = Application()
    # Сыктывкар, Гимназия Искусств
    app.run(app.database_settings)
    sys.exit(0)
