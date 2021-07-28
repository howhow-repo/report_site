from .drive_log_db import *


class Driver(DriveLogDB):
    def __init__(self, ebusMongoDBPath: dict, did: int):
        super().__init__(ebusMongoDBPath)
        self.did = did
