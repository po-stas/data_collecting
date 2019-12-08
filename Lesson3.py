# 1) Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию, записывающую собранные вакансии в созданную БД
# 2) Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой больше введенной суммы
# 3)*Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта

import pandas as pd
from pymongo import errors
from pymongo import MongoClient
from pprint import pprint
from typing import Callable

# будем использовать методы из предыдущего урока для получения данных
from Lesson2 import get_from_sj, get_from_hh


def insert_to_db(df: pd.DataFrame) -> (int, int):
    inserted = 0
    for index, row in df.iterrows():
        if 'hh' in row['Source']:
            collection = hh
        elif 'SuperJob' in row['Source']:
            collection = sj
        else:
            return inserted

        try:
            collection.insert_one(row.to_dict())
            inserted += 1
        except(errors.WriteError, errors.WriteConcernError) as e:
            print('ОШИБКА: Не удалось внести данные %s' % str(row))
            print(e)

    return 0, inserted


# Реализуем функцию, которая будет добавлять только новые вакансии..
# Возможно есть более эффективные варианты - но первое, что попалось под руку update_one с upsert=True
# Понятно, что мы таким образом уже существующие вакансии тоже модифицируем (обновляем до текущего состояния)
# Но по-крайней мере они не будут дублироваться при каждом новом запросе на сайт...
def update_or_insert_to_db(df: pd.DataFrame) -> (int, int):
    inserted = updated = 0
    for index, row in df.iterrows():
        if 'hh' in row['Source']:
            collection = hh
        elif 'SuperJob' in row['Source']:
            collection = sj
        else:
            return inserted, updated

        try:
            result = collection.update_one(filter={'Link': row['Link']}, update={'$set': row.to_dict()},
                                           upsert=True)
            if result.upserted_id:
                inserted += 1
            elif result.modified_count:
                updated += result.modified_count
        except(errors.WriteError, errors.WriteConcernError) as e:
            print('ОШИБКА: Не удалось внести данные %s' % str(row))
            print(e)

    return updated, inserted


def fill_from_web(url: str, pages: int, update_func: Callable) -> int:
    if 'hh.ru' in url:
        data = get_from_hh(url, pages)
    elif 'superjob.ru' in url:
        data = get_from_sj(url, pages)

    updated = inserted = 0
    if data:
        df = pd.DataFrame(data, columns=['Vacancy', 'Link', 'Salary from', 'Salary to', 'Currency', 'Source'])
        df[['Salary from', 'Salary to']] = df[['Salary from', 'Salary to']].apply(pd.to_numeric)
        df['max'] = df[['Salary from', 'Salary to']].max(axis=1)

        updated, inserted = update_func(df)

    return updated, inserted


def print_gte_salary(max_salary: int):
    vacancies = hh.find({'max': {'$gte': max_salary}})
    for vacancy in vacancies:
        pprint(vacancy)

    vacancies.extend = sj.find({'max': {'$gte': 200000}})
    for vacancy in vacancies:
        pprint(vacancy)


# Подключаемся к базе, создаем ДБ и две коллекции
client = MongoClient('localhost', 27017)
db = client['LearningDB']

hh = db.hh
sj = db.sj

# Получаем данные (по одной стриницу с каждого сайта)

fill_from_web(url='https://www.superjob.ru/vacancy/search/?keywords=Python&geo%5Bc%5D%5B0%5D=1',
              pages=1, update_func=insert_to_db)
fill_from_web(url='https://hh.ru/search/vacancy?area=1&st=searchVacancy&text=python&page=0',
              pages=1, update_func=insert_to_db)

# Выборка из базы вакансии с зарплатой больше указанной..
print_gte_salary(200000)

# Пример вывода:

# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/34200113?query=python',
#  'Salary from': 200000.0,
#  'Salary to': nan,
#  'Source': 'hh.ru',
#  'Vacancy': 'Ведущий разработчик Python / Software development / Team lead',
#  '_id': ObjectId('5debe8413ad4784435a48185'),
#  'max': 200000.0}

# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/34850179?query=python',
#  'Salary from': 120000.0,
#  'Salary to': 200000.0,
#  'Source': 'hh.ru',
#  'Vacancy': 'Backend python/Django разработчик',
#  '_id': ObjectId('5debe8423ad4784435a48198'),
#  'max': 200000.0}

# Не очень удобно, что они разнесены в разные колллекции - приходится по-отдельности их опрашивать.
# Но таково было условие задачи ))

# Теперь с функцией обновления базы (добавления только новых вакансий) - возьмем выборку по три страницы с каждого..

fill_from_web(url='https://www.superjob.ru/vacancy/search/?keywords=Python&geo%5Bc%5D%5B0%5D=1',
              pages=3, update_func=update_or_insert_to_db)
fill_from_web(url='https://hh.ru/search/vacancy?area=1&st=searchVacancy&text=python&page=0',
              pages=3, update_func=update_or_insert_to_db)

print_gte_salary(200000)

# Вывод:
# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/34200113?query=python',
#  'Salary from': 200000.0,
#  'Salary to': nan,
#  'Source': 'hh.ru',
#  'Vacancy': 'Ведущий разработчик Python / Software development / Team lead',
#  '_id': ObjectId('5debe8413ad4784435a48185'),
#  'max': 200000.0}

# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/34850179?query=python',
#  'Salary from': 120000.0,
#  'Salary to': 200000.0,
#  'Source': 'hh.ru',
#  'Vacancy': 'Backend python/Django разработчик',
#  '_id': ObjectId('5debe8423ad4784435a48198'),
#  'max': 200000.0}

# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/34643007?query=python',
#  'Salary from': 100000.0,
#  'Salary to': 200000.0,
#  'Source': 'hh.ru',
#  'Vacancy': 'Computer Vision / Data scientist CV',
#  '_id': ObjectId('5debf21db3c5b160cd07cf1b'),
#  'max': 200000.0}

# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/33416348?query=python',
#  'Salary from': nan,
#  'Salary to': 400000.0,
#  'Source': 'hh.ru',
#  'Vacancy': 'Python разработчик / Python software developer',
#  '_id': ObjectId('5debf21db3c5b160cd07cf42'),
#  'max': 400000.0}

# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/30424698?query=python',
#  'Salary from': 220000.0,
#  'Salary to': nan,
#  'Source': 'hh.ru',
#  'Vacancy': 'Senior Python разработчик',
#  '_id': ObjectId('5debf21db3c5b160cd07cf46'),
#  'max': 220000.0}

# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/34405798?query=python',
#  'Salary from': nan,
#  'Salary to': 300000.0,
#  'Source': 'hh.ru',
#  'Vacancy': 'Ведущий программист Python',
#  '_id': ObjectId('5debf21db3c5b160cd07cf4a'),
#  'max': 300000.0}

# {'Currency': 'руб.',
#  'Link': 'https://hh.ru/vacancy/34831620?query=python',
#  'Salary from': 200000.0,
#  'Salary to': 300000.0,
#  'Source': 'hh.ru',
#  'Vacancy': 'Python Web Developer',
#  '_id': ObjectId('5debf21db3c5b160cd07cf59'),
#  'max': 300000.0}

# Новые вакансии добавились в выборку - старые не задублировались. Все работает.
