# Вывести список всех репозиториев конкретного пользователя

import requests
import json
import os

req = requests.get('https://api.github.com/users/po-stas/repos')
if req.ok:
    print(f'Найдено {len(req.json())} репозиториев:')
    for i, repo in enumerate(req.json()):
        print(f'{i+1}. {repo["name"]}')

# Найдено 2 репозиториев:
# 1. data_collecting
# 2. GeekBrains-AI-Course

# Выполнить запрос методом GET к ресурсам, использующим любой тип авторизации через Postman, Python.
# Подключаться будем к imdb.com база данных о кино. Пришлось правда сделать триальную подписку.

url = 'https://movie-database-imdb-alternative.p.rapidapi.com/'
title = 'Stalingrad'
querystring = {'page': '1', 'r': 'json', 's': title}
headers = {
    'x-rapidapi-host': 'movie-database-imdb-alternative.p.rapidapi.com',
    'x-rapidapi-key': os.environ['IMDB_APIKEY']
}

req = requests.request("GET", url, headers=headers, params=querystring)
if req.ok:
    try:
        response = json.loads(req.text)
        results = response['Search']
        print(f'Найдено {len(results)} фильмов {title}:')
        for movie in results:
            print(f'{movie["Title"]}: {movie["Year"]} год.')
    except Exception as e:
        print('Error parsing response')
        print(str(e))
        raise

# Найдено 10 фильмов Stalingrad:
# Stalingrad: 1993 год.
# Stalingrad: 2013 год.
# Stalingrad: 2003– год.
# Stalingrad: Dogs, Do You Want to Live Forever?: 1959 год.
# Stalingrad: 1990 год.
# The Doctor of Stalingrad: 1958 год.
# The City That Stopped Hitler: Heroic Stalingrad: 1943 год.
# Stalingrad: 1963 год.
# Red Orchestra 2: Heroes of Stalingrad: 2011 год.
# The Boy from Stalingrad: 1943 год.

