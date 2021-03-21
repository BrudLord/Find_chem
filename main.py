import sys
from io import BytesIO
from find_spn_param import find_spn
import requests
from PIL import Image, ImageDraw, ImageFont
import math


def lonlat_distance(a, b):
    degree_to_meters_factor = 111 * 1000  # 111 километров в метрах
    a_lon, a_lat = a
    b_lon, b_lat = b
    a_lon = float(a_lon)
    a_lat = float(a_lat)
    b_lat = float(b_lat)
    b_lon = float(b_lon)

    # Берем среднюю по широте точку и считаем коэффициент для нее.
    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)

    # Вычисляем смещения в метрах по вертикали и горизонтали.
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor

    # Вычисляем расстояние между точками.
    distance = math.sqrt(dx * dx + dy * dy)

    return distance


# Пусть наше приложение предполагает запуск:
# python main.py Москва, улица Тимура Фрунзе, 11к8
# Тогда запрос к геокодеру формируется следующим образом:
toponym_to_find = " ".join(sys.argv[1:])

geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "geocode": toponym_to_find,
    "format": "json"}

response = requests.get(geocoder_api_server, params=geocoder_params)

if not response:
    # обработка ошибочной ситуации
    pass

# Преобразуем ответ в json-объект
json_response = response.json()
# Получаем первый топоним из ответа геокодера.
toponym = json_response["response"]["GeoObjectCollection"][
    "featureMember"][0]["GeoObject"]
# Координаты центра топонима:
toponym_coodrinates = toponym["Point"]["pos"]
# Долгота и широта:
toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

search_api_server = "https://search-maps.yandex.ru/v1/"
api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

address_ll = ",".join([toponym_longitude, toponym_lattitude])
search_params = {
    "apikey": api_key,
    "text": "аптека",
    "lang": "ru_RU",
    "ll": address_ll,
    "type": "biz"
}

response = requests.get(search_api_server, params=search_params)
if not response:
    # ...
    pass

# Преобразуем ответ в json-объект
json_response = response.json()
chem = json_response["features"][0]["properties"]
# Получаем первую найденную организацию.
organization = json_response["features"][0]
# Название организации.
org_name = organization["properties"]["CompanyMetaData"]["name"]
# Адрес организации.
org_address = organization["properties"]["CompanyMetaData"]["address"]

# Получаем координаты ответа.
point = organization["geometry"]["coordinates"]
org_point = "{0},{1}".format(point[0], point[1])

deltax, deltay = find_spn(toponym_to_find)

# Собираем параметры для запроса к StaticMapsAPI:
map_params = {
    "l": "map",
    'pt': ",".join([toponym_longitude, toponym_lattitude]) + ',ya_ru~' + "{0},pm2dgl".format(org_point)
}

map_api_server = "http://static-maps.yandex.ru/1.x/"
# ... и выполняем запрос
response = requests.get(map_api_server, params=map_params)

im = Image.open(BytesIO(
    response.content)).convert('RGB')
draw = ImageDraw.Draw(im)
draw.rectangle((0, int(im.size[1] * 0.9), im.size[0], im.size[0]), fill='white')
font = ImageFont.truetype('Marta_Decor_Two.ttf', size=int(im.size[1] * 0.04))
draw.text(
    (5, int(im.size[1] * 0.91)),
    chem['description'],
    font=font,
    fill='#1C0606')
draw.text(
    (5, int(im.size[1] * 0.96)),
    chem['CompanyMetaData']['Hours']['text'],
    font=font,
    fill='#1C0606')
draw.text(
    (int(im.size[0] * 0.5), int(im.size[1] * 0.91)),
    chem['name'],
    font=font,
    fill='#1C0606')
draw.text(
    (int(im.size[0] * 0.5), int(im.size[1] * 0.96)),
    str(int(lonlat_distance([float(toponym_longitude), float(toponym_lattitude)], chem['boundedBy'][0]))) + ' m',
    font=font,
    fill='#1C0606')
im.show()