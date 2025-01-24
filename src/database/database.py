import sqlite3
import numpy as np
import pandas as pd
import json
from src.data_acquisition import XenoCantoRecording
from datetime import datetime

class DatabaseHandler:
    def __init__(self, database_file):
        self.database_file = database_file

    def create_and_connect(self):
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS recordings("
                       "recording_id INTEGER PRIMARY KEY,"
                       "gen_species TEXT,"
                       "specific_species TEXT,"
                       "specific_subspecies TEXT,"
                       "animal_group TEXT,"
                       "en_name TEXT,"
                       "country TEXT,"
                       "location TEXT,"
                       "latitude REAL,"
                       "longitude REAL,"
                       "type TEXT,"
                       "sex TEXT,"
                       "stage TEXT,"
                       "file_url TEXT,"
                       "quality TEXT,"
                       "length REAL,"
                       "datetime TEXT,"
                       "other_species TEXT,"
                       "filename TEXT"
                       ")")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_species ON recordings("
                       "gen_species, "
                       "specific_species)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_location ON recordings("
                       "country, "
                       "location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality ON recordings("
                       "quality)")



        conn.commit()
        return conn

    def _dump_to_json(self, list_to_dump):
        str_list = json.dumps(list_to_dump)
        return str_list
    def _read_from_json(self, str_list):
        return json.loads(str_list)

    def upload_recording(self, recording: XenoCantoRecording):
        conn = self.create_and_connect()
        recording_temp = recording
        recording_temp.other_species = self._dump_to_json(recording_temp.other_species)
        recording_temp.datetime = recording.datetime.strftime("%Y-%m-%d %H:%M:%S")

        recording_dict = recording_temp.__dict__
        fields = ','.join(recording_dict.keys())
        placeholders = ','.join(['?'] * len(recording_dict.keys()))
        values = tuple(recording_dict.values())

        query = (f"INSERT or IGNORE INTO recordings ({fields}) VALUES "
                 f"({placeholders})")

        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()

    def reset_db(self):
        conn = self.create_and_connect()
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS recordings")
        conn.commit()
        conn.close()
