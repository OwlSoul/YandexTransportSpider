# YandexTransportSpider

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

Если отложить в сторону версию "меня адски прет смотреть на разрастающиеся графы" - эта штука просто берет и составляет базу данных общественного транспорта начиная с той точки которую вы ей указали. При этом данные в базе будут "от Яндекса", а это очень много полезной и вкусной информации, которую потом можно использовать **ОФФЛАЙН**. Небольшой изолированый(!!!) город (Якутск, Чита, Сыктывкар... Кы... Кызыл, да храни его господь) "паук" растащит на базу где-то за 6-12 часов при частоте запросов к Яндексу "1 в минуту". Почему так важно что город изолированный? А потому что если запустить эту штуку в Екатеринбурге она со временем найдет маршрут до Челябинска, Кургана и, возможно, Перми, и поползет туда. Про Москву и область и думать страшно. На данный момент "THERE IS NO STOPPING THE SPIDER" и он не успокоится пока не найдет все до чего дотянется. Паука, кстати, можно остановить в любой момент, и потом продолжить указав новую стартовую точку, или ту же самую (он там сам разберется), главное не трогать и не изменять базу - очередь запросов он тоже хранит в ней (бууу, буууу, плохой паттерн, бууууу!!!). Я лично запускаю его на каком-то крупном городе когда выхожу из дома, а вечером прихожу и "прусь на разросшийся граф".

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
_stop_id_ - ID остановки
_name_ - имя остановки
_region_ - регион остановки
_timestamp_ - время, когда остановка была добавлена в базу
_data_ - JSON ответ от getStopInfo Яндекса.

#### Структура таблицы routes:
_route_id_ - ID маршрута
_type_ - тип маршрута (автобус, троллейбус и т.д.)
_name_ - имя маршрута
_region_ - не используется, пока оставлено чтобы "что-то не сломать", потом уберу (никогда)
_timestamp_ - время, когда маршрут был добавлена в базу
_data_ - JSON ответ от getRouteInfo Яндекса.

#### Таблица queue:
Это очередь запросов для "паука", лучше эту штуку не трогать.

_id_ - порядковый номер
_type_ - тип запроса, 'stop' или 'route'
_data_id_ - здесь будет или _stop_id_ остановки, или _route_id_ маршрута
_thread_id_ - маршруту для идентификации нужен еще и ID "линии" (туда, обратно, альтернативная и.т.д).

 </details>
 
 Конец.
