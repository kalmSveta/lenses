import argparse
from read_recepy import *


def parse_args():
    # 1. Создаем парсер аргументов
    parser = argparse.ArgumentParser()
    # 2. Добавляем аргументы
    parser.add_argument("dates", type=str,
                        help="Период дат в формате XX.YY-XX.YY")
    # 3. Читаем аргументы из командной строки
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    recipes_tkl = prepare_recipes(tab='ТКЛ-рецепты',
                                  date_str=parse_args().dates)
    recipes_mfkl = prepare_recipes(tab='МФКЛ-рецепты',
                                   date_str=parse_args().dates)
    print(recipes_tkl[['ФИО Клиента', 'Дата рецепта']].head())
    print(recipes_mfkl[['ФИО Клиента', 'Дата рецепта']].head())
