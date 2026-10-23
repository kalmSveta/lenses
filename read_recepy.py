import pandas as pd
from datetime import datetime
from process_sales import *


def parse_date_range(date_range: str):
    # строка вида "дд.мм.гг-дд.мм.гг", например "01.09.25-30.09.25"
    start_part, end_part = date_range.split("-")
    start_date = datetime.strptime(start_part.strip(), "%d.%m.%y").date()
    end_date = datetime.strptime(end_part.strip(), "%d.%m.%y").date()
    return start_date, end_date


def read_prescriptions(file_prescription, lens_group, paid):
    if paid:
        tab = lens_group + '-рецепты оплаченые'
    else:
        tab = lens_group + '-рецепты'
    prescriptions = pd.read_excel(file_prescription, sheet_name=tab)
    # сделаем все ФИО прописными и уберем первый пробел
    prescriptions['ФИО Клиента'] = prescriptions['ФИО Клиента'].str.lower()
    prescriptions['ФИО Клиента'] = prescriptions['ФИО Клиента'].str.lstrip()
    return prescriptions


def get_patients_with_orders_in_date_range(prescriptions, start_date, end_date):
    # отфильтруем по дате рецепта
    prescriptions['Дата рецепта'] = \
        pd.to_datetime(prescriptions['Дата рецепта']).dt.date
    patients = prescriptions.loc[prescriptions['Дата рецепта'].between(start_date, end_date),
                                 'ФИО Клиента'].tolist()
    patients = list(set(patients))
    return patients


def save_prescriptions_with_bonus(prescriptions, start_date, end_date,
                                  patients_with_prizes, lens_group):
    prescriptions['Премия'] = (
            prescriptions['ФИО Клиента'].isin(patients_with_prizes) &
            prescriptions['Дата рецепта'].between(start_date, end_date)
    ).astype(int)
    output_file_name = lens_group + '_РЕЦЕПТЫ.xlsx'
    prescriptions[['ФИО Клиента', 'Премия']].to_excel(output_file_name, index=False)
    return 0


def get_patients_not_paid(lens_group):
    prescriptions_paid = read_prescriptions(file_prescription='ексели/РЕЦЕПТЫ.xlsx',
                                            lens_group=lens_group,
                                            paid=True)
    patients_paid = set(prescriptions_paid['ФИО Клиента'])
    prescriptions_all = read_prescriptions(file_prescription='ексели/РЕЦЕПТЫ.xlsx',
                                           lens_group=lens_group,
                                           paid=False)
    patients_all = set(prescriptions_all['ФИО Клиента'])
    patients_not_paid = patients_all - patients_paid
    return patients_not_paid


def process_prescriptions(lens_group, start_date, end_date):
    print('Работаю над '+lens_group)
    prescriptions = read_prescriptions(file_prescription='ексели/РЕЦЕПТЫ.xlsx',
                                       lens_group=lens_group,
                                       paid=True)
    print('Всего строк в файле рецепты: '+str(len(prescriptions)))
    patients_paid = get_patients_with_orders_in_date_range(prescriptions=prescriptions,
                                                      start_date=start_date,
                                                      end_date=end_date)
    print('Уникальных пациентов с рецептами за нужные даты: '+str(len(patients_paid)))
    patients_not_paid = get_patients_not_paid(lens_group)
    patients_with_prizes = get_patients_with_prizes(orders_file_path='ексели',
                                                    lens_group=lens_group,
                                                    patients_paid=patients_paid,
                                                    patients_not_paid=patients_not_paid)
    print('Пациентов с призами: '+str(len(patients_with_prizes)))
    save_prescriptions_with_bonus(prescriptions=prescriptions,
                                  start_date=start_date,
                                  end_date=end_date,
                                  patients_with_prizes=patients_with_prizes,
                                  lens_group=lens_group)
