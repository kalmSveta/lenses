import pandas as pd
import calendar
from datetime import datetime


def get_date_range(date_str: str):
    # Разделяем строку на начальную и конечную подстроки
    start_part, end_part = date_str.split("-")
    # Парсим начальную дату (по умолчанию datetime ставит 1-е число)
    start_date = datetime.strptime(start_part.strip(), "%m.%y").date()
    # Парсим конечную дату
    end_date_raw = datetime.strptime(end_part.strip(), "%m.%y").date()
    # Находим последний день для месяца конечной даты
    _, last_day = calendar.monthrange(end_date_raw.year, end_date_raw.month)
    end_date = end_date_raw.replace(day=last_day)
    return start_date, end_date


def prepare_recipes(tab: str, date_str: str):
    # tab = 'ТКЛ-рецепты оплаченые'
    # tab = 'МФКЛ-рецепты оплаченые'
    recipes = pd.read_excel('РЕЦЕПТЫ.xlsx', sheet_name=tab)
    # присвоим уникальный id каждой строке
    recipes['row_id'] = range(len(recipes))
    # отфильтруем по дате рецепта
    start_date, end_date = get_date_range(date_str)
    recipes['Дата рецепта'] = pd.to_datetime(recipes['Дата рецепта']).dt.date
    recipes = recipes.loc[(recipes['Дата рецепта'] >= start_date) &
                          (recipes['Дата рецепта'] <= end_date)]
    # сделаем все ФИО прописными и уберем первый пробел
    recipes['ФИО Клиента'] = recipes['ФИО Клиента'].str.lower()
    recipes['ФИО Клиента'] = recipes['ФИО Клиента'].str.lstrip()
    recipes['Сотрудник'] = recipes['Сотрудник'].str.lower()
    recipes['Сотрудник'] = recipes['Сотрудник'].str.lstrip()
    return recipes
