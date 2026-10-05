import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)


def read_operations(file_name: str):
    df = pd.read_excel(file_name, skiprows=1)
    # # присвоим уникальный id строкам файла
    # df['row_id'] = range(len(df))
    # переименовать столбцы
    df.rename(columns={'Unnamed: 0': 'ФИО Клиента', 'Unnamed: 2': 'id заказа',
                       'Unnamed: 3': 'Линза', 'Unnamed: 4': 'Дата заказа',
                       'Unnamed: 5': 'Дата доплаты'}, inplace=True)
    return df


def preprocess_operations(df):
    # убрать строки с итого
    df = df[~df['ФИО Клиента'].str.contains('Итог', na=False)]
    df = df[~df['Unnamed: 1'].str.contains('Итог', na=False)]
    df = df[~df['Линза'].str.contains('Итог', na=False)]
    df = df[~df['Дата заказа'].str.contains('Итог', na=False)]
    df = df[~df['id заказа'].str.contains('Итог', na=False)]
    # убрать первый пробел и сделать строчными фио
    df['ФИО Клиента'] = df['ФИО Клиента'].str.lower()
    df['ФИО Клиента'] = df['ФИО Клиента'].str.replace(r'^ ', '', regex=True)
    # убрать лишние столбцы
    df = df[['ФИО Клиента', 'id заказа', 'Линза', 'Дата заказа', 'Дата доплаты',
             'Кол-во', 'Сумма платежа', 'Сумма доплаты']]
    # дата и время переделать в дату
    df['Дата заказа'] = pd.to_datetime(df['Дата заказа']).dt.date
    df['Дата доплаты'] = pd.to_datetime(df['Дата доплаты']).dt.date
    return df


def fill_empty_rows(df, column):
    df_copy = df.copy()
    df_copy[column] = df_copy[column].replace(r'^\s*$', pd.NA, regex=True)
    df_copy[column] = df_copy[column].ffill()
    return df_copy


def fill_empty(df):
    df = fill_empty_rows(df, 'ФИО Клиента')
    df = fill_empty_rows(df, 'id заказа')
    df = fill_empty_rows(df, 'Линза')
    df['id заказа'] = df['id заказа'].astype(int)
    return df


def lens_type(df):
    conditions = [
        df['Линза'].str.contains('30', na=False),
        df['Линза'].str.contains('3', na=False),
        df['Линза'].str.contains('6', na=False),
        df['Линза'].str.contains('12', na=False),
        df['Линза'].str.contains('90', na=False)
    ]
    choices = ['1D', 'ПЗ', 'ПЗ', 'ПЗ', 'ПЗ']
    df['Тип линзы'] = np.select(conditions, choices, default=None)
    return df


def use_mfkl_handbook(file_name: str, tab: str, df):
    handbook = pd.read_excel(file_name, sheet_name=tab)
    new_df = pd.merge(df, handbook[['Название КЛ', 'в файле МФКЛ']],
                      left_on='Линза', right_on='Название КЛ', how='left')
    new_df = new_df.drop(columns=['Линза', 'Название КЛ'])
    new_df = new_df.rename(columns={'в файле МФКЛ': 'Линза'})
    return new_df


def count_balls(df):
    # объединяем колонки
    df['Дата'] = np.where(df["Дата заказа"].isna(), df["Дата доплаты"],
                          df["Дата заказа"])
    df['Сумма'] = np.where(df["Сумма платежа"] == 0, df["Сумма доплаты"],
                           df["Сумма платежа"])
    # если клиент, Линза и дата совпадают - то считаем это за 1 заказ
    # (проставить один id)
    df['id заказа новое'] = df['id заказа']
    df["id заказа новое"] = df.groupby(["ФИО Клиента", "Линза", "Дата"])["id заказа новое"].transform("first")
    df = (
        df.groupby(["ФИО Клиента", "id заказа новое"])
        .agg({"Сумма": "sum", "Кол-во": "sum", "Тип линзы": "first"})
        .reset_index()
    )
    # рассчитаем баллы:
    # Для ПЗ:
        # если 1/2 коробки - 1б
        # если >= 3 коробок - 2б
    # Для 1Д:
        # если 1/2 коробки - 0,8б
        # если 3/4 коробки - 1,6б
        # если >=5 коробок - 2,4б
    # Для отрицательных количеств коробок тоже самое, но отрицательные баллы
    conditions = [
        # --- БЛОК ДЛЯ ТИПА ЛИНЗЫ "ПЗ" ---
        (df["Тип линзы"] == "ПЗ") & (df["Сумма"] > 0) & (df["Кол-во"].isin([1, 2])),
        (df["Тип линзы"] == "ПЗ") & (df["Сумма"] > 0) & (df["Кол-во"] >= 3),
        (df["Тип линзы"] == "ПЗ") & (df["Сумма"] < 0) & (df["Кол-во"].isin([-1, -2])),
        (df["Тип линзы"] == "ПЗ") & (df["Сумма"] < 0) & (df["Кол-во"] <= -3),
        # --- БЛОК ДЛЯ ТИПА ЛИНЗЫ "1D" ---
        (df["Тип линзы"] == "1D") & (df["Сумма"] > 0) & (df["Кол-во"].isin([1, 2])),
        (df["Тип линзы"] == "1D") & (df["Сумма"] > 0) & (df["Кол-во"].isin([3, 4])),
        (df["Тип линзы"] == "1D") & (df["Сумма"] > 0) & (df["Кол-во"] >= 5),
        (df["Тип линзы"] == "1D") & (df["Сумма"] < 0) & (df["Кол-во"].isin([-1, -2])),
        (df["Тип линзы"] == "1D") & (df["Сумма"] < 0) & (df["Кол-во"].isin([-3, -4])),
        (df["Тип линзы"] == "1D") & (df["Сумма"] < 0) & (df["Кол-во"] <= -5)
    ]

    # Список соответствующих баллов для каждого условия выше
    choices = [
        1,
        2,
        -1,
        -2,  # Результаты для "ПЗ"
        0.8,
        1.6,
        2.4,
        -0.8,
        -1.6,
        -2.4,  # Результаты для "1D"
    ]
    df["Баллы"] = np.select(conditions, choices, default=0)
    return df


def count_prize(df):
    df = df.groupby("ФИО Клиента", as_index=False)["Баллы"].sum()
    df["Приз"] = np.where(df["Баллы"] >= 2, 1, 0)
    return df


#
# def mark_prizes_all_patients_mfkl():
#     operations = read_operations('МФКЛ.xls')
#     preprocessed_operations = preprocess_operations(operations)
#     preprocessed_operations['Приз'] = None
#     patients = preprocessed_operations['ФИО Клиента'].dropna().unique()
#     for patient in patients[:1]:
#         print(patient)
#         operations_for_patient = select_patient(preprocessed_operations, patient)
#         operations_for_patient = use_mfkl_handbook(
#             'Справочник по контактным линзам.xlsx','Справочник по МФКЛ',
#             operations_for_patient)
    #     sales_without_returns = count_sales_without_returns(
    #         count_sales(operations_for_patient),
    #         count_returns(operations_for_patient),
    #     )
    #     prize = check_prize_by_sales(sales_without_returns)
    #     if prize == 0:
    #         prize = check_prize_by_boxes(operations_for_patient)
    #     if prize == 0:
    #         preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
    #                                     patient, 'Приз'] = 'Нет'
    #     elif prize == 1:
    #         preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
    #                                     patient, 'Приз'] = '2 покупки ПЗ'
    #     elif prize == 2:
    #         preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
    #                                     patient, 'Приз'] = '3 покупки любых'
    #     elif prize == 3:
    #         preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
    #                                     patient, 'Приз'] = '3 коробки ПЗ'
    #     else:
    #         preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
    #                                     patient, 'Приз'] = '5 коробки 1Д'
    #
    # preprocessed_operations.to_excel('output.xlsx', index=False)


operations = read_operations('ТКЛ.xls')
preprocessed_operations = preprocess_operations(operations)
df_filled_rows = fill_empty(preprocessed_operations)
df_lens_types = lens_type(df_filled_rows)
df_balls = count_balls(df_lens_types)
df_prizes = count_prize(df_balls)
preprocessed_operations = pd.merge(preprocessed_operations, df_prizes,
                                   on='ФИО Клиента', how='left')

preprocessed_operations.to_excel('output.xlsx', index=False)


# выводить в красивый ексель полуготовый результат
# сделать для МФКЛ
# совместить с рецептами
# сохранит в красивый ексель
# сделать проверку
# сохранить в красивый ексель
