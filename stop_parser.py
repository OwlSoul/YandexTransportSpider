#!/usr/bin/env python3

import json
import datetime
import sys
import psycopg2
from yandex_transport_webdriver_api import YandexTransportProxy

# TODO: Move these two to API
def form_stop_url(stop_id):
    return 'https://yandex.ru/maps/?masstransit[stopId]=' + stop_id

def parse_stop(yandex_stop_id, db_settings, ytproxy_host, ytproxy_port, force_overwrite=False):
    url = form_stop_url(yandex_stop_id)
    stop_id = yandex_stop_id
    print ("ID: " + yandex_stop_id)

    #stop_id = 'stop__9647487' # Get from CLI instead, or make it a function.
    try:
        conn = psycopg2.connect(dbname=db_settings['db_name'],
                                host=db_settings['db_host'],
                                user=db_settings['db_user'],
                                port=db_settings['db_port'],
                                password=db_settings['db_password'])
    except Exception as e:
        print("Exception (connect to database in parse_stop):" + str(e))
        return 1

    cur = conn.cursor()
    sql_query = "SELECT * FROM stops WHERE stop_id='" + stop_id + "'"
    try:
        cur.execute(sql_query)
        rows = cur.fetchall()
    except Exception as e:
        print("Exception (query existing stop):" + str(e))
        return 1

    if not rows:
        do_insert_stop = True
    else:
        do_insert_stop = False
        print("Stop already in database")
        if not force_overwrite:
            return 2

    try:
        print ("Getting data...")
        proxy = YandexTransportProxy(ytproxy_host, ytproxy_port)
        data = proxy.get_stop_info(url)
        #data = json.load(open('stop_maryino.json', 'r', encoding='utf-8'))
    except Exception as e:
        print("Exception (obtain data):" + str(e))
        return 1
    print("")
    # IMPORTANT! For each step check if failed!

    try:
        stop_id = data['data']['properties']['StopMetaData']['id']
    except Exception as e:
        print("Exception (get stop_id):" + str(e))
        return 1

    # Step 1: Check if current stop is in database,
    #         If not - save current stop data to Database

    # Step 2: Get list of route IDs passing through this stop
    try:
        routes = data['data']['properties']['StopMetaData']['Transport']
    except Exception as e:
        print("Exception (get routes) : ")
        return 1

    stop_name = ''
    try:
        stop_name = data['data']['properties']['StopMetaData']['name']
    except Exception as e:
        print("No stop name in data!")

    print("Stop name:", stop_name)

    region = ''
    try:
        region = data['data']['properties']['StopMetaData']['region']['name']
    except:
        print("No region name in data!")
    print("Region:", region)

    print("")

    if do_insert_stop:
        print("Inserting stop data into database...")
        sql_query = "INSERT INTO stops(stop_id, name, region, timestamp, data) " \
                    "VALUES (" + \
                    "'" + stop_id + "'" + "," + \
                    "'" + stop_name + "'" + "," + \
                    "'" + region + "'" + "," + \
                    "TIMESTAMP '" +str(datetime.datetime.now()) + "'," \
                    "'" + json.dumps(data) + "'" + \
                    ")"
        try:
            cur.execute(sql_query)
        except Exception as e:
            print("Exception (insert stop):" + str(e))
            return 1

        print("Done")
        print("")

    print("Found routes:")
    print("routeId".ljust(25), "threadId".ljust(25), "type".ljust(10), "name".ljust(18), "status")
    queue_values = []

    for i, route in enumerate(routes):
        if not 'name' in route:
            raise Exception('No name in route!')
        if not 'id' in route:
            raise  Exception('No id in route')
        if not 'lineId' in route:
            raise  Exception('No lineId in route')
        if not 'type' in route:
            raise Exception('No type in route')
        print(route['lineId'].ljust(25), route['id'].ljust(25), route['type'].ljust(10), route['name'].ljust(18), end=' ')
        sql_query = "SELECT route_id FROM routes WHERE route_id='" + route['lineId'] + "'"
        try:
            cur.execute(sql_query)
        except Exception as e:
            print("Exception (query routes):" + str(e))
            return 1

        rows = cur.fetchall()
        if not rows:
            sql_query_x = "SELECT data_id FROM queue WHERE data_id='" + route['lineId'] + "' AND type='route'"
            try:
                cur.execute(sql_query_x)
            except Exception as e:
                print("Exception (query queue):" + str(e))
                return 1

            rows_x = cur.fetchall()
            if not rows_x:
                print("NEW")
                queue_values.append([route['lineId'], route['id']])
            else:
                print("QUEUED")
        else:
            print("")

    queue_str = ""
    for i in range(0, len(queue_values) - 1):
        queue_str += "(" + "'route'," + "'" + queue_values[i][0] + "', '" + queue_values[i][1] + "')" + ","
    if queue_values:
        queue_str += "(" + "'route'," + "'" + queue_values[-1][0] + "', '" + queue_values[-1][1] + "')"

    if queue_values:
        try:
            sql_query = "INSERT INTO queue(type, data_id, thread_id) VALUES " + queue_str
            cur.execute(sql_query)
        except Exception as e:
            print("Exception (insert into queue):" + str(e))
            return 1

    print("")

    toponyms = []
    try:
        toponyms = data['data']['toponymSearchResponse']['items']
    except:
        pass
    # Nearest stops: METRO
    nearest_stops = []
    queue_values = []
    try:
        for value in toponyms:
            for stop in value['metro']:
                nearest_stops.append(stop)
            for stop in value['stops']:
                nearest_stops.append(stop)
    except:
        pass

    print("Nearest Stops:")

    for entry in nearest_stops:
        try:
            print(entry['id'].ljust(30), entry['name'].ljust(50), end=' ')
        except:
            pass

        sql_query = "SELECT data_id FROM queue WHERE data_id='" + entry['id'] + "' AND type='stop'"
        cur.execute(sql_query)
        rows = cur.fetchall()
        if not rows:
            print("NEW")
            queue_values.append(entry['id'])
        else:
            print("QUEUED")

    queue_str = ""
    for i in range(0, len(queue_values) - 1):
        queue_str += "(" + "'stop'," + "'" + queue_values[i] + "'" + ")" + ","
    if queue_values:
        queue_str += "(" + "'stop'," + "'" + queue_values[-1] + "'" + ")"

    if queue_values:
        try:
            sql_query = "INSERT INTO queue(type, data_id) VALUES " + queue_str;
            cur.execute(sql_query)
        except:
            print("Exception (insert into queue):" + str(e))
            return 1

    print("")

    conn.commit()
    cur.close()
    conn.close()

    print("STOP " + stop_id + "," + stop_name + " : PARSING COMPLETE!")

    return 0

    # Step 3: For each route check it it's already in database.
    #         If not - perform getRouteInfo, save to database.

    # Step 4: For each route, get list of stops (both directions)
    #         For each stop, check if stop is in database.
    #         If not - add to processing queue.

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #

if __name__ == '__main__':
    result = parse_stop("stop__9647487", force_overwrite=True)