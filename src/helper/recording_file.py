import librosa
import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class Call:
    data : np.ndarray
    duration : int
    sample_rate : int
    max : float
    min : float
    mean : float
    std : float
    filename : str
    species : str