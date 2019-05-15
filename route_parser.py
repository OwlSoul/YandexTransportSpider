#!/usr/bin/env python3

import json
import sys
import datetime
import psycopg2
from yandex_transport_webdriver_api import YandexTransportProxy

def form_route_url(route_id, thread_id):
    return 'https://yandex.ru/maps/?masstransit[lineId]=' + route_id + '&' + \
            'masstransit[threadId]=' + thread_id

def parse_route(yandex_route_id, yandex_thread_id, db_settings, ytproxy_host, ytproxy_port, timeout, force_overwrite=False):
    route_id = yandex_route_id
    thread_id = yandex_thread_id
    url = form_route_url(route_id, thread_id)

    print("Time:", str(datetime.datetime.now()))
    print()

    print("ID:", route_id)

    try:
        conn = psycopg2.connect(dbname=db_settings['db_name'],
                                host=db_settings['db_host'],
                                user=db_settings['db_user'],
                                port=db_settings['db_port'],
                                password=db_settings['db_password'])
    except Exception as e:
        print("Exception (connect to database in parse_route):" + str(e))
        return 1

    cur = conn.cursor()
    sql_query = "SELECT * FROM routes WHERE route_id='" + route_id + "'"
    try:
        cur.execute(sql_query)
        rows = cur.fetchall()
    except Exception as e:
        print("Exception (query existing stop):" + str(e))
        return 1


    if not rows:
        do_insert_route = True
    else:
        do_insert_route = False
        print("Route already in database")
        if not force_overwrite:
            return 2

    try:
        print("Getting data...")
        proxy = YandexTransportProxy(ytproxy_host, ytproxy_port)
        print("URL:", url)
        data = proxy.line(url, timeout=timeout)
        #data = json.load(open('route_troll_10_nsk.json', 'r', encoding='utf-8'))
    except Exception as e:
        print("Exception (obtain data):" + str(e))
        return 1

    try:
        route_id = data['data']['features'][0]['properties']['ThreadMetaData']['lineId']
    except:
        pass

    try:
        thread_id = data['data']['features'][0]['properties']['ThreadMetaData']['id']
    except Exception as e:
        print("Exception (thread_id):" + str(e))
        return 0

    route_type = ""
    try:
        route_type = data['data']['features'][0]['properties']['ThreadMetaData']['type']
    except:
        pass

    route_name = ""
    try:
        route_name = data['data']['features'][0]['properties']['ThreadMetaData']['name']
    except:
        pass

    print("ID      :", route_id)
    print("ThreadID:", thread_id)
    print("Type    :", route_type)
    print("Name    :", route_name)
    print("")

    if do_insert_route:
        print("Inserting stop data into database...")
        sql_query = "INSERT INTO routes(route_id, name, type, timestamp, data) " \
                    "VALUES (" + \
                    "'" + route_id.translate(str.maketrans({"'":r"''"})) + "'" + "," + \
                    "'" + route_name.translate(str.maketrans({"'":r"''"})) + "'" + "," + \
                    "'" + route_type.translate(str.maketrans({"'":r"''"})) + "'" + "," + \
                    "TIMESTAMP '" + str(datetime.datetime.now()) + "'," \
                    "'" + json.dumps(data).translate(str.maketrans({"'":r"''"})) + "'" + \
                    ")"
        try:
            cur.execute(sql_query)
        except Exception as e:
            print("Exception (insert stop):" + str(e))
            return 1

        print("Done")
        print("")

    queue_values = []
    for i, feature in enumerate(data['data']['features'], start=1):
        print("Segment", i)
        for j, segment in enumerate(feature['features'], start=1):
            # This is a point stop
            if 'properties' in segment:
                print(str(j).ljust(3), end='')
                print(segment['properties']['name'].ljust(30), end="")
                if 'StopMetaData' in segment['properties']:
                    print(segment['properties']['StopMetaData']['id'].ljust(20), end="")

                sql_query_x = "SELECT data_id FROM queue WHERE data_id='" + segment['properties']['StopMetaData']['id'] + "' AND type='stop'"
                cur.execute(sql_query_x)
                rows = cur.fetchall()
                if not rows:
                    print("NEW")
                    queue_values.append(segment['properties']['StopMetaData']['id'])
                else:
                    print("QUEUED")

    queue_str = ""
    for i in range(0, len(queue_values) - 1):
        queue_str += "(" + "'stop'," + "'" + queue_values[i] + "'" + ")" + ","
    if queue_values:
        queue_str += "(" + "'stop'," + "'" + queue_values[-1] + "'" + ")"

    if queue_values:
        try:
            sql_query = "INSERT INTO queue(type, data_id) VALUES " + queue_str
            cur.execute(sql_query)
        except Exception as e:
            print("Exception (insert into queue):" + str(e))
            return 1

    conn.commit()
    cur.close()
    conn.close()

    print("ROUTE " + route_id + ", " + route_type + " " + route_name, ": PARSING COMPLETE!")

    return 0

if __name__ == '__main__':
    result = parse_route('2161326720', '2161326720', force_overwrite=True)