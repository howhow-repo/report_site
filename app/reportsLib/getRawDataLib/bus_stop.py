from .drive_log_db import *


class BusStop(DriveLogDB):
    def __init__(self, ebusMongoDBPath: dict, sne: str):
        super().__init__(ebusMongoDBPath)
        self.sne = sne
