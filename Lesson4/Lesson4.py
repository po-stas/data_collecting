from lxml import html
import requests
import time
import pandas as pd
from typing import List, Callable

user_agent = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

mail_ru = 'https://mail.ru'
lenta_ru = 'https://lenta.ru'


def mail_ru_parser(response: str) -> List:
    root = html.fromstring(response)
    news_links = root.xpath('//div[contains(@class, "news-item")]/a/@href')

    news = []
    for link in news_links:
        print(f'Parsing {link}...' )
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


def lenta_ru_parser(response: str) -> List:

    def process_item(item) -> List:
        title = item.xpath('text()')[0]
        link = f"https://lenta.ru{item.xpath('@href')[0]}"
        date = f"{item.xpath('.//time/@title')[0]} : {item.xpath('.//time/text()')[0]}"
        source_name = 'lenta.ru'
        source = 'https://lenta.ru'
        return [title, link, date, source_name, source]

    root = html.fromstring(response)
    news = []

    news_section = root.xpath('//section[@class="row b-top7-for-main js-top-seven"]')[0]
    first_item_a = news_section.xpath('.//h2/a')[0]
    news.append(process_item(first_item_a))

    for item in news_section.xpath('.//div[@class="item"]/a'):
        news.append(process_item(item))

    return news


def parse(link: str, parse_func: Callable) -> List:
    response = requests.get(link, headers=user_agent)
    if response.ok:
        return parse_func(response.text)


########################################################
# Start parsing. mail.ru..
data = parse(link=mail_ru, parse_func=mail_ru_parser)
# Then go to lenta..
data.extend(parse(link=lenta_ru, parse_func=lenta_ru_parser))

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



# Пример вывода:


#                                                 Title                                               Link                       date         Source_name                     Source_link
# 0   МИД Украины вновь рассматривает возможность ра...  https://news.mail.ru/politics/39868861/?fromma...  2019-12-14T14:42:10+03:00                ТАСС             http://www.tass.ru/
# 1   Ефимова высмеяла санкции WADA и предрекла себе...  https://sportmail.ru/news/swimming/39870105/?f...  2019-12-14T15:54:42+03:00            Lenta.Ru  http://lenta.ru/rubrics/sport/
# 2   Сокуров заявил, что ему неинтересны обвинения ...  https://news.mail.ru/society/39871445/?frommail=1  2019-12-14T20:03:14+03:00         Коммерсантъ        http://www.kommersant.ru
# 3   Депутат подарил чиновникам вазелин при открыти...  https://news.mail.ru/politics/39870580/?fromma...  2019-12-14T17:30:10+03:00         РИА Новости               http://www.ria.ru
# 4   Участник «Поля чудес» отгадал слово с ошибкой ...  https://news.mail.ru/society/39870252/?frommai...  2019-12-14T16:41:11+03:00         РИА Новости               http://www.ria.ru
# 5   В США заявили о технологии транспортирования ч...  https://news.mail.ru/society/39869090/?frommai...  2019-12-14T19:00:31+03:00            Lenta.Ru               https://lenta.ru/
# 6   Минфин нашел способ не допустить обналичивания...  https://news.mail.ru/politics/39868763/?fromma...  2019-12-14T13:13:44+03:00              m24.ru               http://www.m24.ru
# 7   58-летняя кикбоксерша нокаутировала 21-летнюю ...  https://sportmail.ru/news/martial-arts/3986957...  2019-12-14T14:40:18+03:00            Lenta.Ru  http://lenta.ru/rubrics/sport/
# 8   Кота, пропавшего в аэропорту, нашли спустя 2 м...  https://news.mail.ru/society/39869133/?frommai...  2019-12-14T13:40:01+03:00     Новости Mail.ru            https://news.mail.ru
# 9     Спутник показал, как две Америки светятся ночью  https://news.mail.ru/society/39856016/?frommai...  2019-12-13T12:13:08+03:00      Погода Mail.ru         https://pogoda.mail.ru/
# 10   «Хаббл» сфотографировал межзвездного «пришельца»  https://news.mail.ru/society/39858505/?frommai...  2019-12-13T14:01:18+03:00      Погода Mail.ru         https://pogoda.mail.ru/
# 11             Братьям Магомедовым собирают новое ОПС  https://news.mail.ru/incident/39866219/?fromma...  2019-12-14T10:38:37+03:00  Газета Коммерсантъ      http://kommersant.ru/daily
# 12     Минюст предложил узаконить роботов-коллекторов  https://news.mail.ru/politics/39867102/?fromma...  2019-12-14T10:06:13+03:00            Известия                   http://iz.ru/
# 13  В сборной России есть два Владимира Ткачева. К...  https://sportmail.ru/news/hockey-europe/39870981/  2019-12-14T18:52:53+03:00             Sport24             https://sport24.ru/
# 14  Судзиловская и Голубкина в провокационных обра...  https://kino.mail.ru/news/52549_sudzilovskaya_...                                   Кино Mail.ru            https://kino.mail.ru
# 15                          Выбрана новая «Мисс мира»        https://lenta.ru/news/2019/12/14/missworld/    14 декабря 2019 : 20:07            lenta.ru                https://lenta.ru
# 16           Украинской гривне предрекли резкий обвал           https://lenta.ru/news/2019/12/14/grivna/    14 декабря 2019 : 20:28            lenta.ru                https://lenta.ru
# 17  Бразильского бойца унесли на носилках после но...              https://lenta.ru/news/2019/12/14/rcc/    14 декабря 2019 : 20:09            lenta.ru                https://lenta.ru
# 18                «Челси» дома проиграл середняку АПЛ     https://lenta.ru/news/2019/12/14/chelseabourn/    14 декабря 2019 : 19:58            lenta.ru                https://lenta.ru
# 19  «Нафтогаз» объяснил рост цен для населения рас...         https://lenta.ru/news/2019/12/14/rasplata/    14 декабря 2019 : 19:56            lenta.ru                https://lenta.ru
# 20      Женщина стала миллионершей из-за ошибки банка  https://lenta.ru/news/2019/12/14/millioner_for...    14 декабря 2019 : 19:49            lenta.ru                https://lenta.ru
# 21  Российские арестанты попытались устроить прово...      https://lenta.ru/news/2019/12/14/provocatsia/    14 декабря 2019 : 19:36            lenta.ru                https://lenta.ru
# 22  Россиянку с инсультом повезли в больницу на по...            https://lenta.ru/news/2019/12/14/vagon/    14 декабря 2019 : 19:25            lenta.ru                https://lenta.ru
# 23  В Германии прокомментировали версию России о р...     https://lenta.ru/news/2019/12/14/germany_maas/    14 декабря 2019 : 19:23            lenta.ru                https://lenta.ru
# 24   Якубович объяснил ошибку в слове на «Поле чудес»          https://lenta.ru/news/2019/12/14/read_it/    14 декабря 2019 : 18:44            lenta.ru                https://lenta.ru
#
# Process finished with exit code 0