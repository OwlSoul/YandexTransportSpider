# YandexTransportSpider

*Why so serious?*

**EN:** This is a "spider crawler" for Yandex Transport. It will start with a given stop, and will "crawl" to any part it can, looking for nearby stops and routes. This is a "for fun" project which also kinda demonstrates capabilities of [Yandex Transport Proxy](https://github.com/OwlSoul/YandexTransportProxy).

**RU:** Это своеобразный "поисковый паук", но для систем общественного транспорта (на данных Yandex Transport). Он стартует с той остановки которую вы ему указали, и начинает "расползаться" куда дотянется, собирая в процессе все близлежащие остановки и маршруты. Проект абсолютно на "повеселиться", и демонстрирует возможности [Yandex Transport Proxy](https://github.com/OwlSoul/YandexTransportProxy).

![Yandex Transport Spider](https://github.com/OwlSoul/Images/raw/master/YandexTransportSpider/screenshot-1.png)
 
<details>
<summary> Click for README in English language</summary>
 Here be dragons
 </details>
 
 
<details>
<summary> Нажмите для README на русском языке </summary>
 
## Зачем оно надо?

Если отложить в сторону версию "меня адски прет смотреть на разрастающиеся графы" - эта штука просто берет и составляет базу данных общественного транспорта начиная с той точки которую вы ей указали. При этом данные в базе будут "от Яндекса", а это очень много полезной и вкусной информации, которую потом можно использовать **ОФФЛАЙН**. 

Небольшой **изолированый**(!!!) город (Якутск, Чита, Сыктывкар... Кы... Кызыл, да храни его господь) "паук" растащит на базу где-то за 6-12 часов при частоте запросов к Яндексу "1 в минуту". Почему так важно что город изолированный? А потому что если запустить эту штуку в Екатеринбурге она со временем найдет маршрут до Челябинска, Кургана и, возможно, Перми, и поползет туда. Про Москву и область и думать страшно. На данный момент "THERE IS NO STOPPING THE SPIDER" и он не успокоится пока не найдет все до чего дотянется. 

Паука, кстати, можно остановить в любой момент, и потом продолжить указав новую стартовую точку, или ту же самую (он там сам разберется), главное не трогать и не изменять базу - очередь запросов он тоже хранит в ней (бууу, буууу, плохой паттерн, бууууу!!!). Я лично запускаю его на каком-то крупном городе когда выхожу из дома, а вечером прихожу и "прусь на разросшийся граф".

 ## И как заставить его работать?
 
 Пауку для работы нужны три вещи:
 1. Работающий интернет (duh)
 2. Запущенный и доступный по сети [Yandex Transport Proxy](https://github.com/OwlSoul/YandexTransportProxy)
 3. Подготовленная база данных.
 
### Запуск Yandex Transport Proxy

Лучше всего запускать прокси на той же машине что и паука, и в докер-контейнере:

```
docker pull owlsoul/ytproxy:latest
docker run -t -d --name ytproxy --restart unless-stopped -p 25555:25555 owlsoul/ytproxy:latest
```

Готово.

### Готовим пауку базу данных

Создаем пользователя:

```
CREATE USER yandex_transport WITH ENCRYPTED PASSWORD 'password';
```

Создаем базу данных, и заполняем ее нужными таблицами, потом даем созданному пользователю абсолютную ВЛАСТЬ:
```
CREATE DATABASE yandex_transport;

\c yandex_transport;

CREATE TABLE stops (
    stop_id varchar PRIMARY KEY,
    name varchar,
    region varchar,
    timestamp timestamptz,
    data jsonb
);

CREATE TABLE ROUTES (
    route_id varchar PRIMARY KEY,
    thread_id varchar,
    name varchar,
    type varchar,
    region varchar,
    timestamp timestamptz,
    data jsonb
);

CREATE TABLE queue (
    id serial PRIMARY KEY,
    type varchar,
    data_id varchar,
    thread_id varchar
);

GRANT ALL PRIVILEGES ON SCHEMA public TO yandex_transport;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO yandex_transport;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO yandex_transport;
GRANT ALL PRIVILEGES ON DATABASE yandex_transport TO yandex_transport;
```

Паук по умолочанию будет работать именно с этой базой и с таким паролем.

### Запуск самого паука

Пауку нужна библиотека [YandexTransportWebdriverAPI-Python](https://github.com/OwlSoul/YandexTransportWebdriverAPI-Python), ну и еще там до кучи барахла всякого, немного.

```
pip3 install psycopg2-binary
pip3 install yandex_transport_webdriver_api
```

Запускаем паука, например с остановки ["Улица Чкалова"](https://yandex.ru/maps/19/syktyvkar/?ll=50.808973%2C61.678116&masstransit%5BstopId%5D=1680722687&mode=stop&z=16) в Сыктывкаре:

```
./transport_spider.py 1680722687 --database yandex_transport
```

Все, паук пополз. Часов через 16 закончит, у вас будет база ВСЕГО общественного транспота города Сыктывкар (по версии Яндекса, он все-таки может чего-то не знать).

### Немного о базе данных
В таблицах stops и routes в базе есть поле _data_ типа _jsonb_. В это поле паук пишет ответ от Яндекса в формате JSON, и там есть ну просто вся необходимая остановка по марштуру (траектория, остальные остановки) или остановке (координаты, проходящие маршруты). Яндекс свой JSON постоянно меняет, и документировать его очень неблагодарное дело, но читается оно достаточно легко и понятно. Примеры можно посмотреть [здесь](https://github.com/OwlSoul/YandexTransportProxy/wiki), паук оперирует методами [getStopInfo](https://github.com/OwlSoul/YandexTransportProxy/wiki/%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80:-getStopInfo) и [getRouteInfo](https://github.com/OwlSoul/YandexTransportProxy/wiki/%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80:-getRouteInfo).

#### Структура таблицы stops:
_stop_id_ - ID остановки \
_name_ - имя остановки \
_region_ - регион остановки \
_timestamp_ - время, когда остановка была добавлена в базу \
_data_ - JSON ответ от getStopInfo Яндекса \

#### Структура таблицы routes:
_route_id_ - ID маршрута \
_type_ - тип маршрута (автобус, троллейбус и т.д.) \
_name_ - имя маршрута \
_region_ - не используется, пока оставлено чтобы "что-то не сломать", потом уберу (никогда) \
_timestamp_ - время, когда маршрут был добавлена в базу \
_data_ - JSON ответ от getRouteInfo Яндекса \

#### Таблица queue:
Это очередь запросов для "паука", лучше эту штуку не трогать.

_id_ - порядковый номер
_type_ - тип запроса, 'stop' или 'route' \
_data_id_ - здесь будет или _stop_id_ остановки, или _route_id_ маршрута \
_thread_id_ - маршруту для идентификации нужен еще и ID "линии" (туда, обратно, альтернативная и.т.д) \

### Параметры командной строки для паука

```
positional arguments:
  stop_id              Starting stop ID

optional arguments:
  -h, --help           запросить о помощи
  -v, --version        запросить версию приложения
  --ytproxy_host HOST  хост Yandex Transport Proxy, по умолчанию 127.0.0.1
  --ytproxy_port PORT  порт Yandex Transport Proxy port, по умолчанию 25555
  --database DB_NAME   имя базы данных, по умолчанию yandex_transport
  --db_host DB_HOST    хост базы данных, по умолчанию localhost
  --db_port DB_PORT    порт базы данных, по умолчанию 5432
  --db_user DB_USER    имя пользователя базы данных, по умолчанию yandex_transport
  --db_password PASS   пароль базы данных, по умолчанию password
  --delay_lower D_LOW  нижний предел задержки между запросами, по умолчанию 40
  --delay_upper D_UP   нижний предел задержки между запросами, по умолчанию 60
```

Главное это указать stop_id. Как его получить? Очень просто.
Нужно "кликнуть" на желаемую остановку в Яндекс.Картах и посмотреть URL остановки в адресной строке браузера. \
Например для остановки "Магазин Мелодия" в Химках:

https://yandex.ru/maps/10758/himki/?ll=37.438354%2C55.891513&masstransit%5BstopId%5D=stop__9680782&mode=stop&z=19

Здесь stop_id это **stop__9680782**. Какой-то определенной логике ID мершрутов и остановок не поддаются, может быть любая строка, порой очень и очень вычурная, так что просто спарсить всю базу данных Яндекса по транспорту перебором не выйдет.

Задержка между запросами (по умолчанию - случайное число в районе 1 минуты) управляется через _--delay_lower_ и _--delay_upper_.

## Визуализатор

Визуализатор ни в коем случае не претендует на какие-то почести в мире ВебДева, это ужасная и уродливая штука собранная на коленке с адской архитектурой просто чтобы следить за работой паука, или посмотреть что оно там натянуло в базу. А еще это _"мое первое приложение на GoLang"_ ©®™, _patent pending_, поэтому... поэтому он такой какой он есть.

Визуализатору требуются двае сторонние библиотеки:
```
go get github.com/lib/pq
go get github.com/tidwall/gjson
```

Конфигурация визцализатора находится в файле config/visualizer-config.json:

```
{
    "listen_host": "127.0.0.1",  
    "listen_port": 8090,
    "preload_data": false,

    "city_name": "KYZYL",
    "center_coords": [51.6959, 94.4709],
    "center_zoom": 12,

    "database": "yandex_transport_kyzyl",
    "db_host": "127.0.0.1",
    "db_port": 5432,
    "db_user": "yandex_transport",
    "db_password": "password",

    "draw_delay": 5,
    "update_interval": 60
}
```

_listen_host_ - хост на котором визуализатор будет слушать \
_listen_port_ - порт на котором визуализатор будет слушать \
_preload_data_ - стоит задать **true** если цель - показать готовую базу, в таком случае при запуске скрипта база будет единожды загружена для дальнейшего отображения пользователю. Если стоит **false** - база будет вычитываться при каждом запросе со стороны фронтедна, этот режим подходит для отображения работы паука "в процессе" и представляет из себя ну абсолютно неоптимизированный кусок кода.

_city_name_ - имя города которое стоит отобразить.
_сenter_coords - координаты куда карта будет "смотреть" при первом запуске.
_сenter_zoom_ - масштаб карты при первом запуске.

Параметры базы данных можно не пояснять, они очевидные.

_draw_delay_ - задержка в миллисекундах между отрисовкой элементов на карте
_update_interval_ - задержка в секундах между полной перерисовкай карты (используется если "preload_data": false)

## Запускаем визуализатор

```
go run visualizer-backend.go
```

Теперь можно зайти на http://localhost:8090/leaflet/leaflet.html и переться на разрастающийся граф.

 </details>
 
## License / Лицензия

**EN:** The code is distributed under MIT licence, AS IS, author do not bear any responsibility for possible problems with usage of this project (but he will be very sad).

**RU:** Исходный код распространяется под лицензией MIT, "как есть (as is)", автор ответственности за возможные проблемы при его использовании не несет (но будет глубоко расстроен).


## Credits / Зал славы
__Project author:__ [Yury D.](https://github.com/OwlSoul) (TheOwlSoul@gmail.com) \
