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
    """
    DataClass to store and handle XenoCanto recordings, acquired from the API
    
    Parameters
    ----------
    
    
    Methods
    ----------
    download_recording()
        Downloads the recording to a specified directory.
    
    Returns
    -------
    None
    
    Notes
    -----
    This class is largely used to keep the association between files and 
    their tags/information. When using XenoCantoAPI, you should use 
    from_json() to create this class. 
    
    See Also
    --------
    XenoCantoAPI
    DatabaseHandler
    """ 
    recording_id : int
    gen_species: str
    specific_species: str
    specific_subspecies: str
    animal_group: str
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
    filename: str = None
    def download_recording(self, folder = RAW_DATA_DIR):
        """
        Downloads specific recording from XenoCanto database.
        Parameters
        ----------
        folder
            Path to save the downloaded recording to.
        Returns
        -------

        """
        try:
            filename = (f"{self.recording_id}_{self.gen_species}_"
                        f"{self.specific_species}_"
                        f"{datetime.strftime(self.datetime, '%Y-%m-%d')}_"
                        f"{self.country}.mp3")

            self.filename = filename

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
        """
        Helper function for parsing length of recording into seconds.
        Parameters
        ----------
        length
            String containing the length of recording in the form of MM:SS.
        Returns
        -------
        int
            Length of recording in seconds.
        """
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
        """
        Helper function for parsing date and time of recording into seconds.
        Parameters
        ----------
        date
            Date of recording in the form of YYYY-mm-dd.
        time
            Time of recording in the form of HH:MM.
        Returns
        -------
        datetime
            Datetime object containing the date and time of recording.
        """
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
        """
        Method to create XenoCantoRecording object from JSON data acquired
        from XenoCantoAPI.
        Parameters
        ----------
        json_data
            JSON data acquired from XenoCantoAPI.
        Returns
        -------

        """
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
            animal_group=json_data["group"],
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
    """
    Class to interact and download data from the XenoCantoApi.
    Intended for use with XenoCantoRecording
    
    Parameters
    ----------

    
    Methods
    ----------
    search_api()
        searches the XenoCanto database for recordings fitting a number of
        arguments. Returns list of XenoCantoRecording objects.
    download_recordings()
        Downloads a list of XenoCantoRecording objects.
    
    Returns
    -------
    XenoCantoRecording
    
    Notes
    -----
    This class is designed to be used with XenoCantoRecording dataclass.
    Once searched, valid recordings are stored in self.recordings and can be
    downloaded using download_recordings().

    
    See Also
    --------
    XenoCantoRecording
    DatabaseHandler
    """ 
    def __init__(self):
        self.base_url = 'https://xeno-canto.org/api/2/recordings'

    def search_api(self, search_term = "", **kwargs):
        """
        Method to search XenoCanto API given a search term and other arguments.
        Parameters
        ----------
        search_term
            Search term to search for, usually a scientific species name.
        kwargs
            Other possible arguments passed to XenoCantoAPI.
            grp: Group such as "birds", "grasshoppers" etc.
            gen: Genus, only necessary if search_term is None.
            cnt: Country
            loc: Locality
            seen: yes/no, was the animal seen
            playback: yes/no, was the animal lured by playback
            box: LAT_MIN,LON_MIN,LAT_MAX,LON_MAX
            type: Type of call or sound recorded, valid tags are:
                aberrant, advertisement call, agonistic call, alarm call,
                begging call, call, calling song, courtship song, dawn song,
                defensive call, distress call, disturbance song, drumming,
                duet, echolocation, feeding buzz, female song, flight call,
                flight song, imitation, mating call, mechanical sound,
                nocturnal flight call, release call, rivalry song, searching song,
                 social call, song, subsong, territorial call
            sex: female or male
            stage: Life stage, valid tags are:
                adult, juvenile, nestling, nymph, subadult
            q: Quality of recording, A to E. Accepts < and >.
            area: Area of the world, valid tags are:
                africa, america, asia, australia, europe
            
        Returns
        -------
        list
            List of XenoCantoRecording objects.
        """
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
        """
        Helper method to download recordings from XenoCanto.
        Parameters
        ----------
        recordings
            list of XenoCantoRecording objects to download.
        Returns
        -------

        """
        for i, recording in enumerate(recordings, 1):
            recording.download_recording()
            print(f'Downloaded recording {i}/{len(recordings)}')
            time.sleep(1)


    def download_recording(self, recording):
        """
        Helper method to download recording from XenoCanto.
        Parameters
        ----------
        recording
            XenoCanto recording object to download.
        Returns
        -------

        """
        print(f'Downloading recording.')
        recording.download_recording()
        time.sleep(1)