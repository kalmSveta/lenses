import argparse
from read_recepy import *
from process_sales import *


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
    recipes_tkl = prepare_recipes(tab='ТКЛ-рецепты оплаченые',
                                  date_str=parse_args().dates)
    print(recipes_tkl[['ФИО Клиента', 'Дата рецепта']].head())
    prizes_tkl = mark_prizes_all_patients(lens_group='ТКЛ',
                                          patients=recipes_tkl['ФИО Клиента'])


    recipes_mfkl = prepare_recipes(tab='МФКЛ-рецепты оплаченые',
                                   date_str=parse_args().dates)
    prizes_mfkl = mark_prizes_all_patients(lens_group='МФКЛ',
                                          patients=recipes_mfkl['ФИО Клиента'])
    print(recipes_mfkl[['ФИО Клиента', 'Дата рецепта']].head())
