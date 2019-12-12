from lxml import html
import requests
import time
import pandas as pd
from typing import List, Callable

user_agent = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

mail_ru = 'https://mail.ru'


def mail_ru_parser(response: str) -> List:
    root = html.fromstring(response)
    news_links = root.xpath('//div[contains(@class, "news-item")]/a/@href')

    news = []
    for link in news_links:
        time.sleep(2)
        try:
            news_response = requests.get(link, headers=user_agent)
            if news_response.ok:
                news_root = html.fromstring(news_response.text)
                title = news_root.xpath('//h1[@class="hdr__inner"]/text()')
                source = news_root.xpath('//a[@class="link color_gray breadcrumbs__link"]/@href')
                source_name = news_root.xpath('//a[@class="link color_gray breadcrumbs__link"]/span/text()')
                date = news_root.xpath('//span[@class="note__text breadcrumbs__text js-ago"]/@datetime')
                news.append([field[0] if field else '' for field in (title, [link], date, source_name, source)])
        except requests.exceptions.MissingSchema:
            continue

    return news


def parse(link: str, parse_func: Callable) -> List:
    response = requests.get(link, headers=user_agent)
    if response.ok:
        return parse_func(response.text)


########################################################
# Start parsing. mail.ru..
data = parse(link=mail_ru, parse_func=mail_ru_parser)

# Put results to DataFrame
if data:
    df = pd.DataFrame(data, columns=['Title', 'Link', 'date', 'Source_name', 'Source_link'])

    # Let's print em
    pd.set_option('display.max_columns', 5)
    pd.set_option('display.max_rows', df.shape[0])
    pd.set_option('display.width', 1200)
    print(df)
else:
    print('Something went wrong. No news for the moment...')


                                                # Title                                               Link                       date        Source_name                     Source_link
# 0   Путин: жизнь требует нового осмысления Констит...  https://news.mail.ru/politics/39846225/?fromma...  2019-12-12T16:46:26+03:00        Коммерсантъ        http://www.kommersant.ru
# 1   Здравствуй, Бугенвиль! На карте мира появилось...  https://news.mail.ru/politics/39835551/?fromma...  2019-12-12T14:24:31+03:00  Аргументы и факты                 https://aif.ru/
# 2   Темнокожая балерина обвинила Большой театр в р...  https://news.mail.ru/society/39845965/?frommail=1  2019-12-12T16:42:33+03:00           Lenta.Ru               https://lenta.ru/
# 3   В Амурской области осудили мужчину, нашедшего ...  https://news.mail.ru/incident/39837396/?fromma...  2019-12-12T13:11:38+03:00        РИА Новости               http://www.ria.ru
# 4   Экс-мэра Москвы Лужкова похоронили на Новодеви...  https://news.mail.ru/society/39844361/?frommail=1  2019-12-12T14:50:46+03:00        РИА Новости               http://www.ria.ru
# 5                Госдума увеличила МРОТ на 850 рублей  https://news.mail.ru/economics/39842657/?fromm...  2019-12-12T13:28:38+03:00               ТАСС             http://www.tass.ru/
# 6   Кот с необычными ушами стал новой звездой Сети...  https://news.mail.ru/society/39847017/?frommai...  2019-12-12T17:31:45+03:00    Новости Mail.ru            https://news.mail.ru
# 7   Собиратель мусора нашел амбру на 700 тысяч дол...  https://news.mail.ru/society/39844024/?frommai...  2019-12-12T14:36:13+03:00    Новости Mail.ru            https://news.mail.ru
# 8   В России может появиться норма об изъятии роди...  https://news.mail.ru/society/39839186/?frommail=1  2019-12-12T10:23:18+03:00        Коммерсантъ        http://www.kommersant.ru
# 9               США испытали запрещенную ДРСМД ракету  https://news.mail.ru/politics/39849186/?fromma...  2019-12-12T20:38:39+03:00        РИА Новости               http://www.ria.ru
# 10               «Чернобыльские» шмели стали обжорами  https://news.mail.ru/society/39846976/?frommai...  2019-12-12T17:27:11+03:00    Новости Mail.ru            https://news.mail.ru
# 11                      Овечкин снова покалечил судью  https://sportmail.ru/news/hockey-nhl/39839019/...  2019-12-12T11:38:51+03:00           Lenta.Ru  http://lenta.ru/rubrics/sport/
# 12  Врачи обнаружили пациентку с раздвижными пальцами  https://news.mail.ru/society/39842604/?frommai...  2019-12-12T14:00:05+03:00              N + 1              https://nplus1.ru/
# 13  Допускает ли Черчесов появление Кокорина или М...  https://sportmail.ru/news/football-euro/39842719/  2019-12-12T20:08:47+03:00     Спорт-Экспресс    http://www.sport-express.ru/
# 14  Госдума запретила штрафовать водителей за сред...  https://auto.mail.ru/article/75526-gosduma_zap...  2019-12-11T16:20:07+03:00            Новости                          /news/
# 15  Звезда «Великолепного века» изменился для роли...  https://kino.mail.ru/news/52543_zvezda_velikol...                                  Кино Mail.ru            https://kino.mail.ru
#
# Process finished with exit code 0