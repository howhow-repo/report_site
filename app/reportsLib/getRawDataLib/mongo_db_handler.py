# coding=utf-8
import pymongo
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self, MongoDBOptions: dict, DBName: str = 'ebus'):
        self.__ebusMongoDBPath = "mongodb://" + \
                                 MongoDBOptions['user'] + ":" + \
                                 MongoDBOptions['password'] + "@" + \
                                 MongoDBOptions['host'] + ":" + \
                                 str(MongoDBOptions['port']) + "/" + \
                                 DBName
        self.DBName = DBName
        self._conn = None

    def connect(self):
        try:
            self._conn = MongoClient(self.__ebusMongoDBPath)
            self.db = self._conn[self.DBName]
            logger.debug("drive DB connected: please remember disconnect after used")
        except Exception as err:
            logger.error("something went wrong")
            raise err

    def disconnect(self):
        if isinstance(self._conn,pymongo.MongoClient):
            self._conn.close()
            self._conn = None
        logger.debug("close drive DB connection")

    def test_connection(self):
        try:
            logger.info(self._conn)
        except Exception as err:
            logger.error("something went wrong")
            raise err

    def list_collections(self):
        try:
            return self.db.collection_names()
        except Exception as err:
            logger.error("something went wrong")
            raise err

    def get_distinct(self, datetime: datetime, collection_type: str, query_cmd: dict, field_name: str):
        datetime = datetime.strftime("%Y-%m-%d")
        collection_name = collection_type + "_" + datetime
        if collection_name in self.db.collection_names():
            return self.db[collection_name].find(query_cmd).distinct(field_name)
        else:
            logger.warning(f"can not find collection name: {collection_name}")
            return []

    def _get_logs(self, datetime: datetime, collection_type: str,
                  query_cmd: dict, projection_cmd: dict = None) -> pd.DataFrame:
        datetime = datetime.strftime("%Y-%m-%d")
        collection_name = collection_type + "_" + datetime
        if collection_name in self.db.list_collection_names():
            logs = []
            for log in self.db[collection_name].find(query_cmd,projection_cmd):
                logs.append(log)
            return pd.json_normalize(logs)
        else:
            logger.warning(f"can not find collection name: {collection_name}")
            return pd.DataFrame()
