# coding=utf-8
import pymysql
import pandas as pd
import logging
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


class CenterDB:
    def __init__(self, sqlOption: dict, DBName: str = "bus"):
        self.__sqlOption = sqlOption
        self.__DBName = DBName
        self._db = None
        self.cursor = None

    def connect(self):
        try:
            self._db = pymysql.connect(host=self.__sqlOption['host'],
                                       port=self.__sqlOption['port'],
                                       user=self.__sqlOption['user'],
                                       password=self.__sqlOption['password'],
                                       database=self.__DBName,
                                       )
            self.cursor = self._db.cursor()
            logger.debug("center DB connected: please remember disconnect after used")
        except Exception as err:
            self.disconnect()
            raise ConnectionError(f"ebus center mysql connection error.\n"
                                  f"{err}")

    def disconnect(self):
        if isinstance(self.cursor,pymysql.cursors.Cursor):
            self.cursor.close()
            self.cursor = None
        if isinstance(self._db,pymysql.Connect):
            self._db.close()
            self._db = None
        # self.cursor.close()
        # self._db.close()
        logger.debug("close center DB connection")

    def test_connection(self):
        try:
            self.cursor.execute('SELECT VERSION()')
            data = self.cursor.fetchone()
            print("Database version : %s " % data)
        except Exception as err:
            self.disconnect()
            raise ConnectionError("ebus center mysql test connection fail.")

    def _get_single_data(self, sql_cmd:str):
        try:
            self.cursor.execute(sql_cmd)
            result = self.cursor.fetchone()
            if result is None:
                return None
            else:
                return result[0]
        except Exception as err:
            logger.error(err)
            self.disconnect()
            raise ConnectionError("get data from ebus center mysql fail")

    def _get_table_data(self, table_name: str, sql_cmd: str = None) -> pd.DataFrame:
        try:
            if sql_cmd is None:
                return pd.read_sql('SELECT * from ' + table_name, self._db)
            else:
                return pd.read_sql(sql_cmd, self._db)
        except Exception as err:
            self.disconnect()
            raise err

    def _delete_data(self, sql_cmd: str = None):
        try:
            sql = sql_cmd
            self.cursor.execute(sql)
            self._db.commit()
        except Exception as err:
            self.disconnect()
            raise err

    def insert_data(self, table_name: str, data: pd.DataFrame):
        try:
            db_data = f"mysql+pymysql://{self.__sqlOption['user']}:{self.__sqlOption['password']}" \
                      f"@{self.__sqlOption['host']}:{self.__sqlOption['port']}/bus?charset=utf8mb4"
            engine = create_engine(db_data)
            data.to_sql(table_name, engine, if_exists='append', index=False)
        except Exception as err:
            self.disconnect()
            raise err
