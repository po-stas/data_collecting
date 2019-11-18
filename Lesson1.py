# Вывести список всех репозиториев конкретного пользователя

import requests

req = requests.get('https://api.github.com/users/po-stas/repos')
if req.ok:
    for repo in req.json():
        print(repo['name'])

# data_collecting
# GeekBrains-AI-Course



