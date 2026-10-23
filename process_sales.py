import pandas as pd
import numpy as np
pd.set_option('future.no_silent_downcasting', True)
pd.set_option('display.max_columns', None)


def read_operations(file_name: str):
    df = pd.read_excel(file_name, skiprows=1)
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
    df['ФИО Клиента'] = df['ФИО Клиента'].str.lstrip()
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
    df = fill_order_date(df)
    df['id заказа'] = df['id заказа'].astype(int)
    return df


def fill_order_date(df):
    # если дата заказа пустая - берем ее из других строк с таким же id заказа.
    # если других строк с таким id нет (или у них тоже нет даты) - оставляем
    # пустой
    df = df.copy()
    date_from_id = df.groupby('id заказа')['Дата заказа'].transform('first')
    df['Дата заказа'] = df['Дата заказа'].fillna(date_from_id)
    return df


def select_patients(df, patients):
    df = df[df['ФИО Клиента'].isin(patients)].copy()
    return df


def add_lens_type(df, lens_group):
    conditions = [
        df['Линза'].str.contains('30 шт', na=False),
        df['Линза'].str.contains('3 шт', na=False),
        df['Линза'].str.contains('6 шт', na=False),
        df['Линза'].str.contains('12 шт', na=False),
        df['Линза'].str.contains('90 шт', na=False)
    ]
    choices = ['1D', 'ПЗ', 'ПЗ', 'ПЗ', 'ПЗ']
    df['Тип линзы'] = np.select(conditions, choices, default=None)
    # если не смогли определить тип линзы - выводим таких в файл
    if len(df[df['Тип линзы'].isna()]) > 0:
        print('ОШИБКА: Не смог определить тип линзы')
        output_file_name = lens_group + '_не_смог_определить_тип_линз.xlsx'
        df[df['Тип линзы'].isna()].to_excel(output_file_name, index=False)
    return df


def use_mfkl_handbook(file_name: str, tab: str, df, lens_group):
    handbook = pd.read_excel(file_name, sheet_name=tab)
    new_df = pd.merge(df, handbook[['Название КЛ', 'в файле МФКЛ']],
                      left_on='Линза', right_on='Название КЛ', how='left')
    if len(new_df[new_df['в файле МФКЛ'].isna()]) > 0:
        print('ОШИБКА: Не нашел линзу в справочнике')
        output_file_name = lens_group + '_не_нашел_линзу_в_справочнике.xlsx'
        new_df[new_df['в файле МФКЛ'].isna()].to_excel(output_file_name, index=False)
    new_df = new_df.drop(columns=['Линза', 'Название КЛ'])
    new_df = new_df.rename(columns={'в файле МФКЛ': 'Линза'})
    return new_df


def union_orders(df):
    # если клиент, линза и дата заказа совпадают - то считаем это за 1 заказ
    # (проставить один id)
    df.loc[:, 'id заказа новое'] = df['id заказа']
    df["id заказа новое"] = df.groupby(["ФИО Клиента", "Линза", "Дата заказа"])[
        "id заказа новое"].transform("first")
    df['id заказа новое'] = np.where(df["id заказа новое"].isna(), df["id заказа"],
                           df["id заказа новое"])
    return df


def count_balls(df):
    # объединяем колонки
    df['Сумма'] = np.where(df["Сумма платежа"] == 0, df["Сумма доплаты"],
                           df["Сумма платежа"])
    # выкидываем заказы, у которых сумма равна 0
    order_sums = df.groupby('id заказа')['Сумма'].transform('sum')
    df = df[order_sums != 0].copy()
    # объединяем заказы
    df = union_orders(df)
    # подготовим сводную таблицу
    df = (
        df.groupby(["ФИО Клиента", "id заказа новое", "Линза"])
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


def get_patients_with_payment(df):
    df['Сумма'] = df['Сумма платежа'] + df['Сумма доплаты']
    patient_sums = df.groupby('ФИО Клиента', as_index=False)['Сумма'].sum()
    patients_really_paid = set(
        patient_sums.loc[patient_sums['Сумма'] > 0, 'ФИО Клиента'])
    return patients_really_paid


def get_patients_with_prizes(orders_file_path, lens_group, patients_paid, patients_not_paid):
    input_file_name = orders_file_path + '/' + lens_group + '.xls'
    operations = read_operations(input_file_name)
    operations = preprocess_operations(operations)
    df_filled_rows = fill_empty(operations)
    # найдем, за каких пациентов положены призы
    df_with_patients_paid = select_patients(df_filled_rows, patients_paid)
    if lens_group == 'МФКЛ':
        df_with_patients_paid = use_mfkl_handbook(
            'Справочник по контактным линзам.xlsx', 'Справочник по МФКЛ',
            df_with_patients_paid, lens_group)
    df_with_patients_paid = add_lens_type(df_with_patients_paid, lens_group)
    df_balls = count_balls(df_with_patients_paid)
    df_prizes = count_prize(df_balls)
    # найдем, каких пациентов мы забыли и считаем неоплаченные, хотя они платили
    df_with_patients_not_paid = select_patients(df_filled_rows, patients_not_paid)
    patients_really_paid = get_patients_with_payment(df_with_patients_not_paid)
    # сохраним файл с пометками о призах и "забытых" пациентах
    operations = pd.merge(operations, df_prizes, on='ФИО Клиента', how='left')
    if len(patients_really_paid) > 0:
        print('ВНИМАНИЕ! Есть пропущенные пациенты с оплатой: ' + str(
            len(patients_really_paid)))
        operations['Проверка'] = None
        operations.loc[
            operations['ФИО Клиента'].isin(patients_really_paid), 'Проверка'] = '%%%%%'
    output_file_name = lens_group + '_output.xlsx'
    operations.to_excel(output_file_name, index=False)
    # вернем пациентов с призами
    patients_with_prizes = operations.loc[operations['Приз'] == 1, 'ФИО Клиента'].tolist()
    return patients_with_prizes


# подумать, что на вход и что на выход по путям до файлов
# сделать установочный exe
