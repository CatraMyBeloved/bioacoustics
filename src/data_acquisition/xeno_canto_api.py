#  bioacoustics
#  Copyright (C) 2025 CatraMyBeloved
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import requests
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from src.config import RAW_DATA_DIR, DATA_DIR

class XenoCantoError(Exception):
    pass
class XenoCantoAPIError(XenoCantoError):
    pass

class XenoCantoParseError(XenoCantoError):
    pass

@dataclass
class XenoCantoRecording:
    recording_id : int
    gen_species: str
    specific_species: str
    specific_subspecies: str
    group: str
    en_name: str
    country: str
    location: str
    latitude: float | None
    longitude: float | None
    type: str
    sex: str
    stage: str
    file_url: str
    quality: str
    length: float
    datetime: datetime
    other_species: str

    def download_recording(self, folder = RAW_DATA_DIR):

        try:
            filename = (f"{self.recording_id}_{self.gen_species}_"
                        f"{self.specific_species}_"
                        f"{datetime.strftime(self.datetime, '%Y-%m-%d')}_"
                        f"{self.country}.mp3")

            full_path = folder / filename

            response = requests.get(self.file_url)

            with open(full_path, 'wb') as f:
                f.write(response.content)
        except requests.RequestException as e:
            raise XenoCantoAPIError(f"Error downloading {self.recording_id}: {e}")
        except OSError as e:
            raise XenoCantoAPIError(f"Error saving {self.recording_id}: {e}")

    @staticmethod
    def _parse_length(length):
        splits = length.split(":")
        match len(splits):
            case 1:
                return int(splits)
            case 2:
                return int(splits[0])*60 + int(splits[1])
            case 3:
                return int(splits[0])*60 + int(splits[1])

    @staticmethod
    def _parse_datetime(date, time):
        if time != '?':
            time = '00:00'

        parsed_dt = None

        time_formats = [
            '%Y-%m-%d-%H:%M:%S',
            '%Y-%m-%d-%H:%M',
            '%Y-%m-%d-%H.%M',
        ]

        date_time = date + '-' + time

        for time_format in time_formats:
            try:
                parsed_dt = datetime.strptime(date_time, time_format)
            except ValueError as e:
                continue
        if parsed_dt == None:
            parsed_dt = datetime.now()
        return parsed_dt

    @classmethod
    def from_json(cls, json_data):
        try:
            lat = float(json_data["lat"]) if json_data.get("lat") else None
            lng = float(json_data["lng"]) if json_data.get("lng") else None
        except ValueError:
            lat, lng = None, None
        return cls(
            recording_id=int(json_data["id"]),
            gen_species=json_data["gen"],
            specific_species=json_data["sp"],
            specific_subspecies=json_data["ssp"],
            group=json_data["group"],
            en_name=json_data["en"],
            country=json_data["cnt"],
            location=json_data["loc"],
            longitude=lng,
            latitude=lat,
            type=json_data["type"],
            sex = json_data["sex"],
            stage=json_data["stage"],
            file_url=json_data["file"],
            quality=json_data["q"],
            length = cls._parse_length(json_data["length"]),
            other_species=json_data["also"],
            datetime=cls._parse_datetime(json_data["date"], json_data["time"])
        )

class XenoCantoAPI:
    def __init__(self):
        self.base_url = 'https://xeno-canto.org/api/2/recordings'

    def search_api(self, search_term, **kwargs):
        time.sleep(1)
        try:
            search_url = self.base_url + f'?query={search_term}+'
            for key, value in kwargs.items():
                search_url += f'{key}:{value}+'
            result = requests.get(search_url)
            result.raise_for_status()
            data = result.json()
            if 'numRecordings' not in data or 'recordings' not in data:
                raise XenoCantoAPIError(f'Invalid data format: {data}')

            print(f'Found {data["numRecordings"]} recordings.')
            print(f'Found {data["numSpecies"]} species.')
            print(f'Current page: {data["page"]}/{data["numPages"]}')
            try:
                page = int(input('What page would you like to access?'))
                if page < 1 or page > data['numPages']:
                    raise ValueError(f'Page must be between 1 and {data["numPages"]}')
                else:
                    search_url += f'&page={page}'
            except ValueError as e:
                raise XenoCantoAPIError() from e


            result = requests.get(search_url)
            data = result.json()
            try:
                recordings = [XenoCantoRecording.from_json(recording) for recording in data['recordings']]

            except (KeyError, ValueError) as e:
                raise XenoCantoParseError(f'Could not parse data: {data}') from e

            return recordings

        except requests.RequestException as e:
            raise XenoCantoAPIError(f'Request failed: {e}') from e


    def download_recordings(self, recordings):
        for i, recording in enumerate(recordings, 1):
            recording.download_recording()
            print(f'Downloaded recording {i}/{len(recordings)}')
            time.sleep(1)


