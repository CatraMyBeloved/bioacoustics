import numpy as np
import librosa
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter
import scipy.signal as signal

def spectral_substraction(noise_sample, y, sr, factor = 1, smoothing = None, return_audio = False):
    """
    Spectral substraction noise removal function. Takes noise sample and
    removes it from the recording.
    Parameters
    ----------
    noise_sample
        Timing of noise sample, in seconds.
    y
        Audio signal, from librosa.load()
    sr
        Sampling rate, in Hz.
    factor
        Amplification factor, defaults to 1.
    smoothing
        Smoothing factor, defaults to None.
    return_audio
        Boolean to return audio signal. Defaults to False.

    Returns
    -------
    np.ndarray
        spectrum, with noise removed.
    optional:
    np.ndarray
        complex audio data, suitable to recreate audio file.

    """
    y_spectrum = librosa.stft(y)
    y_spectrum_db = librosa.amplitude_to_db(y_spectrum)
    phase = np.angle(y_spectrum)
    noise_start = int(noise_sample[0]*sr)
    noise_end = int(noise_sample[1]*sr)
    noise_sample = y[noise_start:noise_end]
    noise_spectrum = librosa.stft(noise_sample)
    noise_power = np.mean(np.abs(noise_spectrum)**2, axis=1)

    if smoothing:
        noise_power = gaussian_filter(noise_power, sigma=smoothing)
    noise_power = noise_power.reshape((-1,1))

    spectrum_power = np.abs(y_spectrum)**2
    spectrum_power_cleaned = spectrum_power - factor * noise_power
    spectrum_power_cleaned = np.maximum(spectrum_power_cleaned, 0)
    spectrum_cleaned_db = librosa.power_to_db(spectrum_power_cleaned)

    if return_audio:
        magnitude = librosa.db_to_amplitude(spectrum_cleaned_db)
        complex_spectrum = magnitude * np.exp(1j * phase)
        return librosa.istft(complex_spectrum)

    return spectrum_cleaned_db

def apply_bandpass(y, sr, lowcut, highcut, order, return_audio = False):
    """
    Applies simple bandpass filter to audio data.
    Parameters
    ----------
    y
        Audio signal, from librosa.load()
    sr
        Sample rate, in Hz.
    lowcut
        lower frequency cutoff, in Hz.
    highcut
        upper frequency cutoff, in Hz.
    order
        filter order, determines steepness of cutoff.
    return_audio
        Boolean to return audio signal. Defaults to False.

    Returns
    -------
    np.ndarray
        spectrum, with bandpass applied.
    optional:
    np.ndarray
        complex audio data, suitable to recreate audio file.
    """
    nyq = 0.5 * sr
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band', output = 'ba')
    y_filtered = signal.filtfilt(b, a, y)

    if return_audio:
        return y_filtered

    y_filtered_spectrum = librosa.stft(y_filtered)
    y_filtered_spectrum_db = librosa.amplitude_to_db(y_filtered_spectrum)
    return y_filtered_spectrum_db

def apply_threshold(y, sr, cutoff, return_audio = False):
    """
    Applies simple threshold filter to audio data.
    Parameters
    ----------
    y
        Audio signal, from librosa.load()
    sr
        Sample rate, in Hz.
    cutoff
        Cutoff amplitude, in dB.
    return_audio
        Boolean to return audio signal. Defaults to False.

    Returns
    -------
    np.ndarray
        spectrum, with threshold applied.
    optional:
    np.ndarray
        complex audio data, suitable to recreate audio file.
    """

    y_spectrum = librosa.stft(y)
    y_spectrum_db = librosa.amplitude_to_db(y_spectrum)
    y_spectrum_db[y_spectrum_db < cutoff] = -80

    phase = np.angle(y_spectrum)
    if return_audio:
        magnitude = librosa.db_to_amplitude(y_spectrum_db)
        complex_spectrum = magnitude * np.exp(1j * phase)
        # return librosa.istft(complex_spectrum)

    return y_spectrum_db