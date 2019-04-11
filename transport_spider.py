#!/usr/bin/env python3

import json
import psycopg2
from route_parser import parse_route
from stop_parser import parse_stop
import signal
import time
import sys
import random

is_running = True

def get_record_from_queue():
    try:
        conn = psycopg2.connect("dbname='yandex_transport' user='yandex_transport' host='localhost' password='password'")
    except Exception as e:
        print("Exception (connect to database):" + str(e))
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

def delete_from_queue(type, data_id):
    try:
        conn = psycopg2.connect("dbname='yandex_transport' user='yandex_transport' host='localhost' password='password'")
    except Exception as e:
        print("Exception (connect to database):" + str(e))
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

def get_queue_size():
    try:
        conn = psycopg2.connect("dbname='yandex_transport' user='yandex_transport' host='localhost' password='password'")
    except Exception as e:
        print("Exception (connect to database):" + str(e))
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
        print("Exception (delete queue item):" + str(e))
        pass
    return result

def sigint_handler(sig, frm):
    global is_running
    print("Signal received:", sig)
    is_running = False


if __name__=='__main__':
    print("SPIDER STARTED")
    signal.signal(signal.SIGINT, sigint_handler)

    # Метро Китая Город, Москва
    #start_id = 'stop__10187979'

    # Якутск, Площадь Ленина
    start_id = '3234683817'

    res = parse_stop(start_id)
    if res == 1:
        sys.exit(1)

    if res!=2:
        for i in range(0, 60):
            if is_running:
                time.sleep(1)

    while is_running:
        query_type, query_data_id, query_thread_id = get_record_from_queue()
        print("Type:", query_type, ";", "ID:", query_data_id)
        if query_data_id is None:
            print("query_data_id is None, I'll stop here.")
            sys.exit(0)

        if query_type == 'stop':
            res = parse_stop(query_data_id)
            if res == 1:
                sys.exit(1)
        elif query_type == 'route':
            res = parse_route(query_data_id, query_thread_id)
            if res == 1:
                sys.exit(1)

        delete_from_queue(query_type, query_data_id)
        try:
            print("Objects in queue:", str(get_queue_size()[0]))
        except:
            pass
        if res != 2:
            wait_time = random.randint(40,60)
        else:
            wait_time = 1
        print("Waiting " + str(wait_time) + " secs.")
        print("---------------------------------------------------------------------------------------------------")
        print("")
        for i in range(0, wait_time):
            if is_running:
                time.sleep(1)

    print("SPIDER TERMINATED")