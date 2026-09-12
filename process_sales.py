import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)


def read_operations(file_name: str):
    df = pd.read_excel(file_name, skiprows=1)
    # # присвоим уникальный id строкам файла
    # df['row_id'] = range(len(df))
    # переименовать столбцы
    df.rename(columns={'Unnamed: 0': 'ФИО Клиента', 'Unnamed: 2': 'Линза',
                       'Unnamed: 3': 'Дата заказа',
                       'Unnamed: 4': 'Дата доплаты'}, inplace=True)
    return df


def preprocess_operations(df):
    # убрать строки с итого
    df = df[~df['ФИО Клиента'].str.contains('Итог', na=False)]
    df = df[~df['Unnamed: 1'].str.contains('Итог', na=False)]
    df = df[~df['Линза'].str.contains('Итог', na=False)]
    df = df[~df['Дата заказа'].str.contains('Итог', na=False)]
    # убрать первый пробел и сделать строчными фио
    df['ФИО Клиента'] = df['ФИО Клиента'].str.lower()
    df['ФИО Клиента'] = df['ФИО Клиента'].str.replace(r'^ ', '', regex=True)
    # убрать лишние столбцы
    df = df[['ФИО Клиента', 'Линза', 'Дата заказа', 'Дата доплаты', 'Кол-во',
             'Сумма платежа', 'Сумма доплаты']]
    # дата и время переделать в дату
    df['Дата заказа'] = pd.to_datetime(df['Дата заказа']).dt.date
    df['Дата доплаты'] = pd.to_datetime(df['Дата доплаты']).dt.date

    return df


def select_patient(df, patient):
    mask = df['ФИО Клиента'].eq(patient)

    if mask.any():
        start_pos = df.index.get_loc(df.index[mask][0])
        empty = df['ФИО Клиента'].isna() | df['ФИО Клиента'].astype(
            str).str.strip().eq('')
        tail = empty.iloc[start_pos:].copy()
        tail.iloc[0] = True
        result = df.iloc[start_pos:][tail.cumprod().astype(bool)]
        return result


def lens_type(df):
    conditions = [
        df['Линза'].str.contains('30 шт', na=False),
        df['Линза'].str.contains('3 шт', na=False),
        df['Линза'].str.contains('6 шт', na=False),
        df['Линза'].str.contains('12 шт', na=False),
        df['Линза'].str.contains('90 шт', na=False)
    ]
    choices = ['1D', 'ПЗ', 'ПЗ', 'ПЗ', 'ПЗ']
    df['Тип линзы'] = np.select(conditions, choices, default=None)
    return df


def count_sales(df):
    # заполним названия линз, чтобы не было пустых строк
    df['Линза'] = df['Линза'].replace(r'^\s*$', pd.NA, regex=True)
    df['Линза'] = df['Линза'].ffill()
    # оставляем только строки с платежами либо с доплатами
    df = df.loc[
        (
                (df['Дата заказа'].notna()) & (df['Сумма платежа'] > 0)
        ) | (
                (df['Дата доплаты'].notna()) & (df['Сумма доплаты'] > 0)
        ),
        ['Линза', 'Дата заказа', 'Дата доплаты']
    ]
    # вместо двух колонок с доплатами и платежами делаем одну
    df['Дата'] = df['Дата заказа'].fillna(df['Дата доплаты'])
    df = df[['Линза', 'Дата']]
    # убираем строки, в которых за 1 и ту же линзу платили в один и тот же день
    df = df.drop_duplicates()
    # считаем количество продаж для каждого типа линз
    df = lens_type(df)
    df = df.groupby('Тип линзы').size().reset_index(name='Продажи')
    return df


def count_returns(df):
    df = df.loc[(df['Сумма платежа'] < 0) | (df['Сумма доплаты'] < 0)]
    df = lens_type(df)
    df = df.groupby('Тип линзы').size().reset_index(name='Возвраты')
    return df


def count_sales_without_returns(sales, returns):
    df = pd.merge(sales, returns, on='Тип линзы', how='left')
    df = df.fillna(0)
    df['Итого продаж'] = df['Продажи'] - df['Возвраты']
    return df


def check_prize_by_sales(df):
    # Если 2 и более покупки ПЗ
    if ((df['Тип линзы'] == 'ПЗ') & (df['Итого продаж'] >= 2)).any():
        return 1
    # Если 3 и более покупки любых
    elif df['Итого продаж'].sum() >= 3:
        return 2
    else:
        return 0


def check_prize_by_boxes(df):
    df = lens_type(df)
    df = df.groupby('Тип линзы')['Кол-во'].sum().reset_index()
    # Если в одной покупке 3 и более коробки ПЗ
    if ((df['Тип линзы'] == 'ПЗ') & (df['Кол-во'] >= 3)).any():
        return 3
    # Если в одной покупке 5 и более коробок 1д
    if ((df['Тип линзы'] == '1D') & (df['Кол-во'] >= 5)).any():
        return 4
    else:
        return 0


operations = read_operations('ТКЛ.xls')
preprocessed_operations = preprocess_operations(operations)
preprocessed_operations['Приз'] = None
patients = preprocessed_operations['ФИО Клиента'].dropna().unique()

for patient in patients:
    print(patient)
    operations_for_patient = select_patient(preprocessed_operations, patient)
    sales_without_returns = count_sales_without_returns(
        count_sales(operations_for_patient),
        count_returns(operations_for_patient),
    )
    prize = check_prize_by_sales(sales_without_returns)
    if prize == 0:
        prize = check_prize_by_boxes(operations_for_patient)
    if prize == 0:
        preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
                                    patient, 'Приз'] = 'Нет'
    elif prize == 1:
        preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
                                    patient, 'Приз'] = '2 покупки ПЗ'
    elif prize == 2:
        preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
                                    patient, 'Приз'] = '3 покупки любых'
    elif prize == 3:
        preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
                                    patient, 'Приз'] = '3 коробки ПЗ'
    else:
        preprocessed_operations.loc[preprocessed_operations['ФИО Клиента'] ==
                                    patient, 'Приз'] = '5 коробки 1Д'

preprocessed_operations.to_excel('output.xlsx', index=False)


# сделать для МФКЛ
# совместить с рецептами
# сохранит в красивый ексель
# сделать проверку
# сохранить в красивый ексель
