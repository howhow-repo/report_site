import json

import pandas as pd
import requests
from decouple import config
from datetime import datetime
from center_db import CenterDB

sql_options = json.loads(config("EBUS_SQLDB"))


def format_to_sql(d: dict) -> dict:
    d['date'] = datetime.strptime(d['date'], '%Y/%m/%d')

    if d['name'] == '':
        d['name'] = None

    if d['isHoliday'] == "否":
        d['isHoliday'] = 0
    else:
        d['isHoliday'] = 1

    if d['holidayCategory'] == "星期六、星期日":
        d['holidayCategory'] = 'weekend'
        d['holidayCategoryType'] = 1
    elif d['holidayCategory'] == "放假之紀念日及節日":
        d['holidayCategory'] = 'nationalHoliday'
        d['holidayCategoryType'] = 2
    elif d['holidayCategory'] == "調整放假日":
        d['holidayCategory'] = 'bridgeHoliday'
        d['holidayCategoryType'] = 3
    elif d['holidayCategory'] == "補假":
        d['holidayCategory'] = 'makeUpHoliday'
        d['holidayCategoryType'] = 4
    elif d['holidayCategory'] == "補行上班日":
        d['holidayCategory'] = 'makeUpDay'
        d['holidayCategoryType'] = 5
    elif d['holidayCategory'] == "特定節日":
        d['holidayCategory'] = 'specificHoliday'
        d['holidayCategoryType'] = 6
    del d['description']

    return d


class GovCalendar:
    """
        government calendar api
        to fetch the json data of Taiwan government office calendar.
        for checking if date is holiday or not.

        get:
        https://data.ntpc.gov.tw/api/datasets/308DCD75-6434-45BC-A95F-584DA4FED251/json?page={page}&size={size}
    """
    page = 1
    size = 100000  # api use page & size as args. STUPID DESIGN!
    url = 'https://data.ntpc.gov.tw/api/datasets/308DCD75-6434-45BC-A95F-584DA4FED251/json'

    @classmethod
    def gov_api(cls, page, size) -> dict:
        resp = requests.get(cls.url + f'?page={page}&size={size}')
        dict_data = resp.json()
        return dict_data

    @classmethod
    def keep_as_file(cls, pathname, json_string):
        with open(f"{pathname}", 'w') as file:
            file.write(json_string)

    @classmethod
    def pull_latest_year(cls) -> pd.DataFrame:
        raw_list = cls.gov_api(page=1, size=9999)
        latest_year = datetime.strptime(raw_list[-1]['date'], '%Y/%m/%d').year
        year_list = []

        for d in raw_list:
            if datetime.strptime(d['date'], '%Y/%m/%d').year == latest_year:
                year_list.append(format_to_sql(d))
        df = pd.DataFrame(year_list)
        return df

    @classmethod
    def dump_to_sql(cls):
        new_df = cls.pull_latest_year()
        old_df = cls.get_celendar_from_sql()
        exsist_dates = [int(v.timestamp()) for v in old_df.to_dict()['date'].values()]
        update_data = []

        for d in new_df.to_dict('records'):
            if int(d.get('date').timestamp()) not in exsist_dates:
                update_data.append(d)
        df = pd.DataFrame(update_data)

        db = CenterDB(sql_options)
        db.connect()
        db.insert_data(table_name='calendar', data=df)
        db.disconnect()

    @classmethod
    def get_celendar_from_sql(cls) -> pd.DataFrame:
        db = CenterDB(sql_options)
        db.connect()
        df = db._get_table_data('calendar')
        db.disconnect()
        return df


if __name__ == '__main__':
    df = GovCalendar.dump_to_sql()



    # db = CenterDB(sql_options)
    # db.connect()
    # df = db._get_table_data('calendar')
    # db.disconnect()
    # l = df.to_json()
    # [print(d) for d in json.loads(l)]



    # GovCalendar.keep_as_file(f'{"."}/calendar_cache_file', 'aaaa')

