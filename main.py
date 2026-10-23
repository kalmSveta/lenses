import argparse
from read_recepy import *


def parse_args():
    # 1. Создаем парсер аргументов
    parser = argparse.ArgumentParser()
    # 2. Добавляем аргументы
    parser.add_argument("dates", type=str,
                        help="Период дат в формате ДД.ММ.ГГ-ДД.ММ.ГГ")
    # 3. Читаем аргументы из командной строки
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    # ПОЛУЧАЕМ ДАТЫ
    start_date, end_date = parse_date_range(parse_args().dates)

    # СНАЧАЛА ОБРАБОТАЕМ ТКЛ
    process_prescriptions(lens_group='ТКЛ', start_date=start_date,
                          end_date=end_date)

    # ПОТОМ ОБРАБОТАЕМ МФКЛ
    # process_prescriptions(lens_group='МФКЛ', start_date=start_date,
    #                       end_date=end_date)
