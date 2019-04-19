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
 
# Зачем оно надо?

Если отложить в сторону версию "меня адски прет смотреть на разрастающиеся графы" - эта штука просто берет и составляет базу данных общественного транспорта начиная с той точки которую вы ей указали. При этом данные в базе будут "от Яндекса", а это очень много полезной и вкусной информации, которую потом можно использовать **ОФФЛАЙН**. Небольшой изолированый(!!!) город (Якутск, Чита, Сыктывкар... Кы... Кызыл, да храни его господь) "паук" растащит на базу где-то за 6-12 часов при частоте запросов к Яндексу "1 в минуту". Почему так важно что город изолированный? А потому что если запустить эту штуку в Екатеринбурге она со временем найдет маршрут до Челябинска, Кургана и, возможно, Перми, и поползет туда. Про Москву и область и думать страшно. На данный момент "THERE IS NO STOPPING THE SPIDER" и он не успокоится пока не найдет все до чего дотянется. Паука, кстати, можно остановить в любой момент, и потом продолжить указав новую стартовую точку, или ту же самую (он там сам разберется), главное не трогать и не изменять базу - очередь запросов он тоже хранит в ней (бууу, буууу, плохой паттерн, бууууу!!!). Я лично запускаю его на каком-то крупном городе когда выхожу из дома, а вечером прихожу и "прусь на разросшийся граф".

 # И как заставить его работать?
 
 Пауку для работы нужны три вещи:
 1. Работающий интернет (duh)
 2. Запущенный и доступный по сети [Yandex Transport Proxy](https://github.com/OwlSoul/YandexTransportProxy)
 3. Подготовленная база данных.
 
## Запуск Yandex Transport Proxy

Лучше всего запускать прокси на той же машине что и паука, и в докер-контейнере:

```
docker pull owlsoul/ytproxy:latest
docker run -t -d --name ytproxy --restart unless-stopped -p 25555:25555 owlsoul/ytproxy:latest
```

 </details>
 
 Конец.
