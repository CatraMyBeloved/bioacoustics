import librosa
import numpy as np
import pandas as pd
from dataclasses import dataclass
from librosa import feature
from matplotlib import pyplot as plt
import sqlite3
import yaml
from pathlib import Path
#TODO: Named Rows and general structural improvements and resilience for
#TODO: Add isolating calls to either dataclass or general package

@dataclass
class Call:
    """
    Dataclass to store and analyze bird call recordings, or any other audio signal.
    
    Parameters
    ----------
    filename: str
        Path to audio file.
    samplerate: int
        Audio sampling rate, defaults to librosa standard 22050.
    species: str
        Species name, defaults to Unknown.
    duration: float
        Duration in seconds, defaults to 0.
    data: np.ndarray
        Audio data, defaults to None. Loaded from file using librosa.load().
    spectrum: np.ndarray
        Precomputed spectrum, defaults to None. Calculated upon initialization.


    
    Returns
    -------
    None
    
    Notes
    -----
    Filename format should be: XXXXXX_species_date_country.mp3
    XXXXXX is a unique numeric identifier

    Features are calculated using librosa, focusing on typical bird call
    frequencies.

    See Also
    --------
    librosa.load()
    """ 
    filename: str
    recording_id: int
    samplerate: int = None
    species: str = "Unknown"
    en_name: str = "Unknown"
    country: str = "Unknown"
    location: str = "Unknown"
    sex: str = "Unknown"
    duration: float = 0
    data: np.ndarray = None
    spectrum: np.ndarray = None

    def __post_init__(self):
        """
        Performs post_initialization. Reads data from filename and stores it
        in self.data, gets species from filename, gets duration in seconds
        and creates a short term fourier transform.

        Returns
        -------

        """
        config = self.load_config()
        try:
            self.recording_id = int(self.filename[:5])
        except ValueError:
            print("Invalid recording ID/filename format")
            return None

        self.samplerate = config["audio"]["samplerate"]

        root_dir = Path(__file__).parents[2]
        self.database_file = root_dir / config["database"]["filename"]

        if not Path(self.filename).exists():
            raise FileNotFoundError(f"Audio file not found: {self.filename}")
        self.data, self.samplerate = librosa.load(self.filename,
                                               sr=self.samplerate)

        self.spectrum = librosa.amplitude_to_db(librosa.stft(self.data))

        database_result = self._get_from_db()

        if database_result:
            self.species = database_result[2]
            self.en_name = database_result[5]
            self.country = database_result[6]
            self.location = database_result[7]
            self.sex = database_result[11]
            self.duration = float(database_result[15])
            #FIXME: This sucks, use named columns

    def load_config(self):
        """
        Load configuration from yaml file.

        Returns
        -------
        dict
            Configuration dictionary from yaml file

        Raises
        ------
        FileNotFoundError
            If config.yaml is not found
        yaml.YAMLError
            If yaml file is malformed
        """
        config_path = Path(__file__).parents[2] / 'config.yaml'
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found at {config_path}")

    def _get_from_db(self):
        try:
            with sqlite3.connect(self.database_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM recordings where recording_id = ?",
                               (self.recording_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None


    def mean(self) -> np.floating:
        """
        Returns the mean amplitude of the recording,
        
        Parameters
        ----------
        

        Returns
        -------
        np.floating
            Mean amplitude of the recording

        Notes
        -----
        Mean is equivalent to average "loudness" of recording.
        
        See Also
        --------
        std
        """ 
        return np.mean(self.data)
    def std(self) -> np.floating:
        """
        Returns the standard deviation of the recording, equivalent to the spread of loudness.

        Parameters
        ----------


        Returns
        -------
        np.floating
         Standard deviation of the recording, equivalent to the spread of
         loudness.

        Notes
        -----


        See Also
        --------
        mean
        """
        return np.std(self.data)

    def centroid(self) -> np.ndarray:
        """
        Calculates the spectral centroid of the recording.
        
        Parameters
        ----------
        
        
        Returns
        -------
        np.ndarray
         Array of spectral centroid values over time, representing the
         "center of mass" for the spectrum.
        
        Notes
        -----
        The spectral centroid represents the "center of mass" for a sound.
        It is associated with the "brightness" of a sound.
        
        See Also
        --------
        
        """ 
        centroid = librosa.feature.spectral_centroid(y=self.data,
                                                     sr=self.samplerate)[0]
        return centroid

    def show_spectrum(self):
        """
        Displays a dB-based visualization of a STFT (Short-term Fourier Transform) for the audio signal.

        Parameters
        ----------


        Returns
        -------
        plt.figure
            Matplotlib figure object containing the STFT visualization.

        Notes
        -----
        A STFT Spectrum shows the amplitude of different frequencies in the
        sound. It can be understood as a decomposition of the sound into its
        different frequencies, with their amplitudes shown.

        See Also
        --------
        self.spectrum
        """
        fig, ax = plt.subplots(figsize=(12, 4))

        librosa.display.specshow(self.spectrum, sr=self.samplerate, ax=ax,
                                 cmap='coolwarm', x_axis='time', y_axis='hz')

        fig.show()
        return fig
    def examine_features(self):
        """
        Creates a visualization of different features of the audio recording

        Parameters
        ----------


        Returns
        -------
        plt.figure

        Notes
        -----
        Listed features: MFCCs, Spectral Centroid, Bandwith, Rolloff, Zero Crossing Rate, RMS Energy.

        See Also
        --------
        centroid
        show_spectrum
        """
        mfccs = librosa.feature.mfcc(y=self.data, sr=self.samplerate, n_mfcc=8,
                                     n_fft=512,
                                     hop_length=512, fmin= 4000, fmax = 8000)
        centroid = librosa.feature.spectral_centroid(y=self.data,
                                                     sr=self.samplerate)[0]
        bandwidth = librosa.feature.spectral_bandwidth(y=self.data,
                                                       sr=self.samplerate)[0]
        rolloff = librosa.feature.spectral_rolloff(y=self.data,
                                                   sr=self.samplerate)[0]
        zcr = librosa.feature.zero_crossing_rate(self.data)[0]
        rms = librosa.feature.rms(y=self.data)[0]

        fig, ax = plt.subplots(6, 1, figsize=(15, 6*4))

        ax[0].set_title('Centroid')
        ax[0].plot(centroid)

        ax[1].set_title('Bandwidth')
        ax[1].plot(bandwidth)

        ax[2].set_title('Rolloff')
        ax[2].plot(rolloff)

        ax[3].set_title('Zero Crossing Rate')
        ax[3].plot(zcr)

        ax[4].set_title('RMS Energy')
        ax[4].plot(rms)

        ax[5].set_title('MFCCS')
        librosa.display.specshow(mfccs, sr=self.samplerate, ax=ax[5],
                                 x_axis='time', y_axis='hz', cmap='coolwarm')

        fig.show()

        return fig








