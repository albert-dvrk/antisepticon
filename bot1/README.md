💰 Веб-приложение для получения курсов валют от ЦБ РФ.

Запуск через Docker
bash
docker build -t currency-bot .
docker run -d -p 5000:5000 --name currency-bot currency-bot
