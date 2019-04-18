#!/usr/bin/env python3

import psycopg2
import sys
import time

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
        conn.close()
        sys.exit(1)

    result = None
    sql_query = "SELECT id, type, data_id, thread_id FROM queue LIMIT 10"
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        result = cur.fetchall()
    except Exception as e:
        print("Exception (delete queue item):" + str(e))
        pass

    conn.close()

    return result

if __name__ == '__main__':
    while True:
        queue = get_queue(database_settings)
        for i, line in enumerate(queue):
            print(i, ":", line)
        print("")
        time.sleep(delay_time)