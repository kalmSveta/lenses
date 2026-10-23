import argparse
from read_recepy import *


def parse_args():
    # 1. Создаем парсер аргументов
    parser = argparse.ArgumentParser()
    # 2. Добавляем аргументы
    parser.add_argument("dates", type=str,
                        help="Период дат в формате ДД.ММ.ГГ-ДД.ММ.ГГ")
    parser.add_argument("input_folder", type=str,
                        help="Абсолютный путь до папки с входными файлами")
    parser.add_argument("output_folder", type=str,
                        help="Абсолютный путь до папки с выходными файлами")
    # 3. Читаем аргументы из командной строки
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    # ПОЛУЧАЕМ ДАТЫ
    start_date, end_date = parse_date_range(parse_args().dates)

    # СНАЧАЛА ОБРАБОТАЕМ ТКЛ
    input_folder = parse_args().input_folder
    output_folder = parse_args().output_folder
    process_prescriptions(orders_file_path=input_folder,
                          prescription_file_path=input_folder,
                          handbook_file_path=input_folder,
                          lens_group='ТКЛ',
                          start_date=start_date,
                          end_date=end_date,
                          output_file_path=output_folder)

    # ПОТОМ ОБРАБОТАЕМ МФКЛ
    process_prescriptions(orders_file_path=input_folder,
                          prescription_file_path=input_folder,
                          handbook_file_path=input_folder,
                          lens_group='МФКЛ',
                          start_date=start_date,
                          end_date=end_date,
                          output_file_path=output_folder)
