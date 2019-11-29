# Урок 2. Парсинг HTML. BeautifulSoup
# 1) Необходимо собрать информацию о вакансиях на вводимую должность (используем input или через аргументы) с сайта
# superjob.ru и hh.ru. Приложение должно анализировать несколько страниц сайта(также вводим через input или аргументы).
# Получившийся список должен содержать в себе минимум:
#     *Наименование вакансии
#     *Предлагаемую зарплату (отдельно мин. и отдельно макс.)
#     *Ссылку на саму вакансию
#     *Сайт откуда собрана вакансия
# По своему желанию можно добавить еще работодателя и расположение. Данная структура должна быть одинаковая для
# вакансий с обоих сайтов. Общий результат можно вывести с помощью dataFrame через pandas.

from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd


def parse_compensation(comp):
    salary_from = salary_to = units = ''
    comp_search = re.search('(от)?([0-9 ]+)?(до|-)?([0-9 ]+)? (.*)$', comp.replace('\xa0', ''))
    if comp_search:
        if comp_search.group(2):
            salary_from = int(comp_search.group(2))
        if comp_search.group(3) and '-' in comp_search.group(3) or comp_search.group(3) and 'до' in comp_search.group(3):
            salary_to = int(comp_search.group(4))
        elif comp_search.group(1) and 'до' in comp_search.group(1):
            salary_to = int(comp_search.group(2))

        units = comp_search.group(5)
    return salary_from, salary_to, units


def get_from_hh(link):
    # with open('hh.html', 'r') as file:
    #     html = file.read()
    user_agent = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
    req = requests.get(link, headers=user_agent)
    if req.ok:
        html = req.text
        parsed_html = bs(html, 'lxml')

        vacancies = parsed_html.find_all('div', {'class': 'vacancy-serp-item'})
        vacancies_data = []
        for vacancy in vacancies:
            vacancy_data = []
            name = vacancy.find('div', {'class': 'resume-search-item__name'})
            comp = vacancy.find('div', {'class': 'vacancy-serp-item__compensation'})
            try:
                a = name.findChildren('a', {'data-qa': 'vacancy-serp__vacancy-title'})
                vacancy_data.append(a[0].getText())
                vacancy_data.append(a[0]['href'])

                comp_text = ''
                if comp:
                    comp_text = comp.getText()

                salary_from, salary_to, units = parse_compensation(comp_text)
                vacancy_data.extend((salary_from, salary_to, units))

                vacancy_data.append('hh.ru')
                vacancies_data.append(vacancy_data)

            except Exception:
                continue

    return vacancies_data


def get_from_sj(link):

    with open('SuperJob2.html', 'r') as file:
        html = file.read()

    parsed_html = bs(html, 'lxml')
    vacancies = parsed_html.find_all('div', {'class': '_3zucV _2GPIV f-test-vacancy-item i6-sc _3VcZr'})

    vacancies_data = []
    for vacancy in vacancies:
        vacancy_data = []
        a = vacancy.findChildren('a', {'class': '_1QIBo'})
        link = a[0]['href']
        title_block = a[0].findChildren('div', {'class': '_3mfro'})
        title = ''.join(title_block[0].findAll(text=True, recursive=True))
        print(title)
        salary_block = vacancy.findChildren('span', {'class': '_2Wp8I'})
        if salary_block:
            salary = salary_block[0].getText().replace('\xa0—\xa0', '-')
            salary = re.sub(r'(\d+)\xa0(\d+)', r'\1\2', salary).replace('\xa0', ' ')
            salary_from, salary_to, units = parse_compensation(salary)
        pass


get_from_sj('')
# data = get_from_hh('https://hh.ru/search/vacancy?area=1&st=searchVacancy&text=python')


# if data:
#     df = pd.DataFrame(data, columns=['Вакансия', 'Ссылка', 'ЗП от', 'ЗП до', 'валюта', 'Источник'])
#     pd.set_option('display.max_columns', 6)
#     pd.set_option('display.width', 1000)
#     print(df)
# else:
#     print('Ничего не найдено...')
