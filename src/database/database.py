import sqlite3
import numpy as np
import pandas as pd
import json
from src.data_acquisition import XenoCantoRecording
from datetime import datetime
class DatabaseHandler:
    """
    Handles connecting and inserting data into recordings Database

    Parameters
    ----------


    Returns
    -------
    None

    Notes
    -----
    Creates and adds entries to sqlite database. Cannot remove entries.

    See Also
    --------

    """
    def __init__(self, database_file):

        self.database_file = database_file

    def create_and_connect(self):
        """
        Connects to database, creates table if not existant.
        Returns
        -------
        sqlite3.Connection
            Connection to database
        """
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
        """
        Helper method to dump list to json
        Parameters
        ----------
        list_to_dump
            list to dump to json string
        Returns
        -------
        str
            String containing json formatted list
        """
        str_list = json.dumps(list_to_dump)
        return str_list
    def _read_from_json(self, str_list):
        """
        Helper method to read from json
        Parameters
        ----------
        str_list
            string containing json formatted list
        Returns
        -------

        """
        return json.loads(str_list)

    def upload_recording(self, recording: XenoCantoRecording):
        """
        Method to upload recording data to database
        Parameters
        ----------
        recording
            XenoCantoRecording object optained from XenoCantoAPI

        Returns
        -------
        None
        """
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
        """
        Helper method to reset database
        Returns
        -------
        None
        """
        conn = self.create_and_connect()
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS recordings")
        conn.commit()
        conn.close()
