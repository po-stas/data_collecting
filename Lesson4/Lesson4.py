from lxml import html
import requests
import pandas as pd

user_agent = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

mail_ru = 'https://mail.ru'
response = requests.get(mail_ru, headers=user_agent)
if response.ok:
    root = html.fromstring(response.text)
    news_links = root.xpath('//div[contains(@class, "news-item")]/a/@href')
    # news_titles = root.xpath('//div[contains(@class, "news-item")]/a/text()')

    for link in news_links:
        news_response = requests.get(link, headers=user_agent)
        if news_response.ok:
            news_root = html.fromstring(news_response.text)
            title = news_root.xpath('//h1[@class="hdr__inner"]/text()')
            source = news_root.xpath('//a[@class="link color_gray breadcrumbs__link"]/@href')
            source_name = news_root.xpath('//a[@class="link color_gray breadcrumbs__link"]/span/text()')
            date = news_root.xpath('//span[@class="note__text breadcrumbs__text js-ago"]/@datetime')
            print(date)

