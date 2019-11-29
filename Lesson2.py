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
import time
import pandas as pd
from typing import List


# Парсер полей ЗП
def parse_compensation(comp: str) -> List:
    salary_from = salary_to = units = ''
    comp_search = re.search('(от)?([0-9 ]+)?(до|-)?([0-9 ]+)? (.*)$', comp.lower().replace('\xa0', ''))
    if comp_search:
        if comp_search.group(2):
            salary_from = int(comp_search.group(2))
        if comp_search.group(3) and '-' in comp_search.group(3) or comp_search.group(3) and 'до' in comp_search.group(3):
            salary_to = int(comp_search.group(4))
        elif comp_search.group(1) and 'до' in comp_search.group(1):
            salary_to = int(comp_search.group(2))
        if salary_to or salary_from:
            units = comp_search.group(5)

    return salary_from, salary_to, units


def get_from_hh(url: str, pages: int) -> List[List[str]]:
    # with open('hh.html', 'r') as file:
    #     html = file.read()
    user_agent = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

    vacancies_data = []

    for page in range(pages):
        req = requests.get(url, headers=user_agent)
        if req.ok:
            print(url + '...')
            html = req.text
            parsed_html = bs(html, 'lxml')

            vacancies = parsed_html.find_all('div', {'class': 'vacancy-serp-item'})

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

        else:
            break

        time.sleep(5)
        url = url[:-1] + str(page + 1)

    return vacancies_data


def get_from_sj(url: str, pages: int) -> List[List[str]]:

    # with open('SuperJob2.html', 'r') as file:
    #     html = file.read()

    user_agent = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

    vacancies_data = []

    for page in range(pages):
        req = requests.get(url, headers=user_agent)
        if req.ok:
            print(url + '...')
            html = req.text

            parsed_html = bs(html, 'lxml')
            vacancies = parsed_html.find_all('div', {'class': '_3zucV _2GPIV f-test-vacancy-item i6-sc _3VcZr'})

            for vacancy in vacancies:
                vacancy_data = []
                try:
                    a = vacancy.findChildren('a', {'class': '_1QIBo'})
                    link = a[0]['href']
                    title_block = a[0].findChildren('div', {'class': '_3mfro'})
                    title = ''.join(title_block[0].findAll(text=True, recursive=True))

                    vacancy_data.extend((title, 'https://www.superjob.ru' + link))

                    salary_block = vacancy.findChildren('span', {'class': '_2Wp8I'})
                    if salary_block:
                        salary = salary_block[0].getText().replace('\xa0—\xa0', '-')
                        salary = re.sub(r'(\d+)\xa0(\d+)', r'\1\2', salary).replace('\xa0', ' ')
                        vacancy_data.extend(parse_compensation(salary))

                    vacancy_data.append('SuperJob.ru')
                    vacancies_data.append(vacancy_data)
                except Exception:
                    continue

        else:
            break

        time.sleep(5)
        url = url[:-1] + str(page + 2)

    return vacancies_data


# Получаем данные
data = get_from_sj('https://www.superjob.ru/vacancy/search/?keywords=Python&geo%5Bc%5D%5B0%5D=1', 3)
data.extend(get_from_hh('https://hh.ru/search/vacancy?area=1&st=searchVacancy&text=python&page=0', 3))


if data:
    df = pd.DataFrame(data, columns=['Вакансия', 'Ссылка', 'ЗП от', 'ЗП до', 'валюта', 'Источник'])

    # Сортируем. Наибольшая зп сверху
    df[['ЗП от', 'ЗП до']] = df[['ЗП от', 'ЗП до']].apply(pd.to_numeric)
    df['max'] = df[['ЗП от', 'ЗП до']].max(axis=1)
    df.sort_values(by=['max'], ascending=False, inplace=True)
    df.drop('max', axis=1, inplace=True)
    df.loc[df['ЗП от'].isnull(), 'ЗП от'] = ''
    df.loc[df['ЗП до'].isnull(), 'ЗП до'] = ''

    # Выводим
    pd.set_option('display.max_columns', 6)
    pd.set_option('display.max_rows', df.shape[0])
    pd.set_option('display.width', 1200)
    print(df)
else:
    print('Ничего не найдено...')

# Не знаю имеет ли смысл приводить здесь - пример запуска:
# https://www.superjob.ru/vacancy/search/?keywords=Python&geo%5Bc%5D%5B0%5D=1...
# https://www.superjob.ru/vacancy/search/?keywords=Python&geo%5Bc%5D%5B0%5D=2...
# https://www.superjob.ru/vacancy/search/?keywords=Python&geo%5Bc%5D%5B0%5D=3...
# https://hh.ru/search/vacancy?area=1&st=searchVacancy&text=python&page=0...
# https://hh.ru/search/vacancy?area=1&st=searchVacancy&text=python&page=1...
# https://hh.ru/search/vacancy?area=1&st=searchVacancy&text=python&page=2...
#                                               Вакансия                                             Ссылка   ЗП от   ЗП до валюта     Источник
# 79      Python разработчик / Python software developer        https://hh.ru/vacancy/33416348?query=python          400000   руб.        hh.ru
# 84                          Ведущий программист Python        https://hh.ru/vacancy/34405798?query=python          300000   руб.        hh.ru
# 27   Специалист обработки естественных языков и ком...  https://www.superjob.ru/vakansii/specialist-ob...  150000  300000      ₽  SuperJob.ru
# 47   Специалист обработки естественных языков и ком...  https://www.superjob.ru/vakansii/specialist-ob...  150000  300000      ₽  SuperJob.ru
# 91                                Python Web Developer        https://hh.ru/vacancy/33895741?query=python  200000  300000   руб.        hh.ru
# 80                                  Python разработчик        https://hh.ru/vacancy/34790452?query=python  180000  250000   руб.        hh.ru
# 73                      Junior Quantitative Researcher        https://hh.ru/vacancy/31844648?query=python  250000  250000   руб.        hh.ru
# 65       Senior Frontend Developer (JavaScript, React)        https://hh.ru/vacancy/34746892?query=python  230000           руб.        hh.ru
# 70                                  Программист Python        https://hh.ru/vacancy/34668861?query=python  120000  220000   руб.        hh.ru
# 82             Старший разработчик (Python) / TeamLead        https://hh.ru/vacancy/34750253?query=python  180000  210000   руб.        hh.ru
# 101                                   Python developer        https://hh.ru/vacancy/34397072?query=python  150000  200000   руб.        hh.ru
# 71                                    Python developer        https://hh.ru/vacancy/34483790?query=python  160000  200000   руб.        hh.ru
# 69   Ведущий разработчик Python / Software developm...        https://hh.ru/vacancy/34200113?query=python  200000           руб.        hh.ru
# 117                Computer Vision / Data scientist CV        https://hh.ru/vacancy/34643007?query=python  100000  200000   руб.        hh.ru
# 76                        Ведущий разработчик (Python)        https://hh.ru/vacancy/34750132?query=python  150000  180000   руб.        hh.ru
# 86                          Специалист по Data Science        https://hh.ru/vacancy/34209978?query=python  172500  172500   руб.        hh.ru
# 25                          Специалист по Data Science  https://www.superjob.ru/vakansii/specialist-po...  172000  172000      ₽  SuperJob.ru
# 45                          Специалист по Data Science  https://www.superjob.ru/vakansii/specialist-po...  172000  172000      ₽  SuperJob.ru
# 44                                    Reverse Engineer  https://www.superjob.ru/vakansii/reverse-engin...  170000              ₽  SuperJob.ru
# 16                                         Программист  https://www.superjob.ru/vakansii/programmist-3...  170000              ₽  SuperJob.ru
# 62             Data scientist (ML разработчик, python)        https://hh.ru/vacancy/34029220?query=python  140000  170000   руб.        hh.ru
# 64                                      Data Scientist        https://hh.ru/vacancy/33204430?query=python  170000           руб.        hh.ru
# 24                                    Reverse Engineer  https://www.superjob.ru/vakansii/reverse-engin...  170000              ₽  SuperJob.ru
# 74                                  Разработчик Python        https://hh.ru/vacancy/34805442?query=python   90000  160000   руб.        hh.ru
# 113                                     Data Scientist        https://hh.ru/vacancy/34728304?query=python          150000   руб.        hh.ru
# 85                                  Python разработчик        https://hh.ru/vacancy/34467339?query=python  100000  150000   руб.        hh.ru
# 72                                Разработчик (Python)        https://hh.ru/vacancy/34749955?query=python  120000  150000   руб.        hh.ru
# 108               Python-разработчик/ Python Developer        https://hh.ru/vacancy/34627413?query=python   80000  150000   руб.        hh.ru
# 98              Javascript разработчик (Junior/Middle)        https://hh.ru/vacancy/34744072?query=python  120000  150000   руб.        hh.ru
# 119                 Программист Python Django (Middle)        https://hh.ru/vacancy/34221879?query=python  100000  150000   руб.        hh.ru
# 68                   Backend-разработчик (PHP/Symfony)        https://hh.ru/vacancy/34418956?query=python          150000   руб.        hh.ru
# 53                 Администратор баз данных PostgreSQL  https://www.superjob.ru/vakansii/administrator...  150000              ₽  SuperJob.ru
# 9                         Старший back-end разработчик  https://www.superjob.ru/vakansii/starshij-back...  150000              ₽  SuperJob.ru
# 33                 Администратор баз данных PostgreSQL  https://www.superjob.ru/vakansii/administrator...  150000              ₽  SuperJob.ru
# 81                            Программист Python (ГИС)        https://hh.ru/vacancy/34410063?query=python  140000           руб.        hh.ru
# 102                            Программист Python, C++        https://hh.ru/vacancy/34800575?query=python   90000  140000   руб.        hh.ru
# 17                                         Программист  https://www.superjob.ru/vakansii/programmist-3...  140000              ₽  SuperJob.ru
# 96                                  Разработчик Python        https://hh.ru/vacancy/34733084?query=python  130000           руб.        hh.ru
# 88    Python Developer / разработчик Python (удаленно)        https://hh.ru/vacancy/34649041?query=python          130000   руб.        hh.ru
# 78                                  Программист Python        https://hh.ru/vacancy/34799714?query=python   80000  130000   руб.        hh.ru
# 105  Python/Django разработчик / Python/Django deve...        https://hh.ru/vacancy/34467194?query=python  120000           руб.        hh.ru
# 107                                   Python developer        https://hh.ru/vacancy/34705551?query=python   80000  120000   руб.        hh.ru
# 95                        Младший разработчик (Python)        https://hh.ru/vacancy/34550242?query=python   90000  120000   руб.        hh.ru
# 112                          Программист Python/Django        https://hh.ru/vacancy/34400390?query=python  120000           руб.        hh.ru
# 93                                 Инженер-тестировщик        https://hh.ru/vacancy/34510318?query=python  100000  120000   руб.        hh.ru
# 15                         Инженер по автотестированию  https://www.superjob.ru/vakansii/inzhener-po-a...  115000              ₽  SuperJob.ru
# 103                        Python разработчик (Django)        https://hh.ru/vacancy/34650379?query=python   70000  100000   руб.        hh.ru
# 22                                 Инженер-программист  https://www.superjob.ru/vakansii/inzhener-prog...  100000              ₽  SuperJob.ru
# 114                                 Разработчик Python        https://hh.ru/vacancy/34462285?query=python  100000           руб.        hh.ru
# 29   Преподаватель компьютерных IT-курсов, программ...  https://www.superjob.ru/vakansii/prepodavatel-...  100000              ₽  SuperJob.ru
# 118                                    Веб-разработчик        https://hh.ru/vacancy/34754242?query=python   70000  100000   руб.        hh.ru
# 30   Разработчик в отдел технических средств обучен...  https://www.superjob.ru/vakansii/razrabotchik-...   60000  100000      ₽  SuperJob.ru
# 42                                 Инженер-программист  https://www.superjob.ru/vakansii/inzhener-prog...  100000              ₽  SuperJob.ru
# 7                                  Инженер-программист  https://www.superjob.ru/vakansii/inzhener-prog...  100000              ₽  SuperJob.ru
# 50   Разработчик в отдел технических средств обучен...  https://www.superjob.ru/vakansii/razrabotchik-...   60000  100000      ₽  SuperJob.ru
# 49   Преподаватель компьютерных IT-курсов, программ...  https://www.superjob.ru/vakansii/prepodavatel-...  100000              ₽  SuperJob.ru
# 106               Аналитик (SQL, Python, VBA) антифрод        https://hh.ru/vacancy/33816278?query=python           85000   руб.        hh.ru
# 52      Ведущий системный администратор Linux (Zabbix)  https://www.superjob.ru/vakansii/veduschij-sis...   70000              ₽  SuperJob.ru
# 32      Ведущий системный администратор Linux (Zabbix)  https://www.superjob.ru/vakansii/veduschij-sis...   70000              ₽  SuperJob.ru
# 54                             Системный администратор  https://www.superjob.ru/vakansii/sistemnyj-adm...   64000              ₽  SuperJob.ru
# 34                             Системный администратор  https://www.superjob.ru/vakansii/sistemnyj-adm...   64000              ₽  SuperJob.ru
# 89                              Junior Web разработчик        https://hh.ru/vacancy/34504195?query=python   20000   60000   руб.        hh.ru
# 1                            Программист Perl / Python  https://www.superjob.ru/vakansii/programmist-p...   45000   45000      ₽  SuperJob.ru
# 51                                 Инженер-программист  https://www.superjob.ru/vakansii/inzhener-prog...   40000              ₽  SuperJob.ru
# 31                                 Инженер-программист  https://www.superjob.ru/vakansii/inzhener-prog...   40000              ₽  SuperJob.ru
# 83                                    Python developer        https://hh.ru/vacancy/30005963?query=python    4000            usd        hh.ru
# 109                     Senior Python разработчик (GO)        https://hh.ru/vacancy/34644534?query=python    3000            eur        hh.ru
# 104                  Python Golang Backend Devops Lead        https://hh.ru/vacancy/34656892?query=python    3000            eur        hh.ru
# 75                                    Python developer        https://hh.ru/vacancy/34664551?query=python    2000    3000    usd        hh.ru
# 0                                   Программист Python  https://www.superjob.ru/vakansii/programmist-p...                         SuperJob.ru
# 2                                      Аналитик Python  https://www.superjob.ru/vakansii/analitik-pyth...                         SuperJob.ru
# 3                                   Разработчик Python  https://www.superjob.ru/vakansii/razrabotchik-...                         SuperJob.ru
# 4                                Программист на python  https://www.superjob.ru/vakansii/programmist-n...                         SuperJob.ru
# 5                   Специалист программирования Python  https://www.superjob.ru/vakansii/specialist-pr...                         SuperJob.ru
# 6        Администратор тестовых сред (ведущий инженер)  https://www.superjob.ru/vakansii/administrator...                         SuperJob.ru
# 8                                 Финансовый контролер  https://www.superjob.ru/vakansii/finansovyj-ko...                         SuperJob.ru
# 10                               Web-разработчик React  https://www.superjob.ru/vakansii/web-razrabotc...                         SuperJob.ru
# 11                Тестировщик программного обеспечения  https://www.superjob.ru/vakansii/testirovschik...                         SuperJob.ru
# 12        Специалист по автоматизации бизнес-процессов  https://www.superjob.ru/vakansii/specialist-po...                         SuperJob.ru
# 13                     Ведущий системный администратор  https://www.superjob.ru/vakansii/veduschij-sis...                         SuperJob.ru
# 14                       Системный администратор Linux  https://www.superjob.ru/vakansii/sistemnyj-adm...                         SuperJob.ru
# 18                     Старший инженер по тестированию  https://www.superjob.ru/vakansii/starshij-inzh...                         SuperJob.ru
# 19                               Инженер Devops Stream  https://www.superjob.ru/vakansii/inzhener-devo...                         SuperJob.ru
# 20                                     Аналитик Python  https://www.superjob.ru/vakansii/analitik-pyth...                         SuperJob.ru
# 21                               Программист на python  https://www.superjob.ru/vakansii/programmist-n...                         SuperJob.ru
# 23                Тестировщик программного обеспечения  https://www.superjob.ru/vakansii/testirovschik...                         SuperJob.ru
# 26                        Главный аналитик (SQL, OLAP)  https://www.superjob.ru/vakansii/glavnyj-anali...                         SuperJob.ru
# 28                             Системный администратор  https://www.superjob.ru/vakansii/sistemnyj-adm...                         SuperJob.ru
# 35                         Аналитик по прогнозированию  https://www.superjob.ru/vakansii/analitik-po-p...                         SuperJob.ru
# 36                       Системный администратор Linux  https://www.superjob.ru/vakansii/sistemnyj-adm...                         SuperJob.ru
# 37                           QA engineer (Тестировщик)  https://www.superjob.ru/vakansii/qa-engineer-3...                         SuperJob.ru
# 38                          Разработчик Oracle PL, SQL  https://www.superjob.ru/vakansii/razrabotchik-...                         SuperJob.ru
# 39                                         Программист  https://www.superjob.ru/vakansii/programmist-3...                         SuperJob.ru
# 40                                     Аналитик Python  https://www.superjob.ru/vakansii/analitik-pyth...                         SuperJob.ru
# 41                               Программист на python  https://www.superjob.ru/vakansii/programmist-n...                         SuperJob.ru
# 43                Тестировщик программного обеспечения  https://www.superjob.ru/vakansii/testirovschik...                         SuperJob.ru
# 46                        Главный аналитик (SQL, OLAP)  https://www.superjob.ru/vakansii/glavnyj-anali...                         SuperJob.ru
# 48                             Системный администратор  https://www.superjob.ru/vakansii/sistemnyj-adm...                         SuperJob.ru
# 55                         Аналитик по прогнозированию  https://www.superjob.ru/vakansii/analitik-po-p...                         SuperJob.ru
# 56                       Системный администратор Linux  https://www.superjob.ru/vakansii/sistemnyj-adm...                         SuperJob.ru
# 57                           QA engineer (Тестировщик)  https://www.superjob.ru/vakansii/qa-engineer-3...                         SuperJob.ru
# 58                          Разработчик Oracle PL, SQL  https://www.superjob.ru/vakansii/razrabotchik-...                         SuperJob.ru
# 59                                         Программист  https://www.superjob.ru/vakansii/programmist-3...                         SuperJob.ru
# 60            Junior data engineer (внедрение моделей)        https://hh.ru/vacancy/33774758?query=python                               hh.ru
# 61                               Data Analyst (Senior)        https://hh.ru/vacancy/33864288?query=python                               hh.ru
# 63                             Аналитик/Data Scientist        https://hh.ru/vacancy/34428700?query=python                               hh.ru
# 66          Scala Developer (Java / C++ / С# / Python)        https://hh.ru/vacancy/33070488?query=python                               hh.ru
# 67                                DevOps/Linux-инженер        https://hh.ru/vacancy/33563753?query=python                               hh.ru
# 77                              Аналитик (Python, SQL)        https://hh.ru/vacancy/34511131?query=python                               hh.ru
# 87                                    Python Developer        https://hh.ru/vacancy/34422508?query=python                               hh.ru
# 90                               Python Developer (ML)        https://hh.ru/vacancy/28570434?query=python                               hh.ru
# 92                                  Разработчик Python        https://hh.ru/vacancy/33549408?query=python                               hh.ru
# 94                                    Python Developer        https://hh.ru/vacancy/34343070?query=python                               hh.ru
# 97                                    Python Developer        https://hh.ru/vacancy/34590659?query=python                               hh.ru
# 99   Аналитик - эконометрист / Data scientist (Juni...        https://hh.ru/vacancy/34391782?query=python                               hh.ru
# 100                                Python/Go Developer        https://hh.ru/vacancy/34567979?query=python                               hh.ru
# 110                                 Программист Python        https://hh.ru/vacancy/34505036?query=python                               hh.ru
# 111                         Data Sсientist (ML/Python)        https://hh.ru/vacancy/33481247?query=python                               hh.ru
# 115                                 Разработчик Python        https://hh.ru/vacancy/33582706?query=python                               hh.ru
# 116                                   Python Developer        https://hh.ru/vacancy/32878639?query=python                               hh.ru
#
# Process finished with exit code 0

