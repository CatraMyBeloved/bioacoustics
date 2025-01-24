import numpy as np
import librosa
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter
import scipy.signal as signal

from sklearn.preprocessing import StandardScaler

def scale_features(feature_dict):
    # Convert dictionary to flat array
    features = np.concatenate([
        feature_dict['mfcc_means'],
        feature_dict['mfcc_stds'],
        [feature_dict['centroid_mean'],
         feature_dict['centroid_std'],
         feature_dict['rolloff_mean'],
         feature_dict['rolloff_std'],
         feature_dict['rms_mean'],
         feature_dict['rms_std']]
    ])

    # Scale features
    scaler = StandardScaler()
    features = features.reshape(-1, 1)
    scaler.fit(features)
    scaled_features = scaler.transform(features, copy = True)
    return scaled_features

def build_dataset(files):
    all_features = []
    all_labels = []

    for audio_file in files:
        y, sr = librosa.load('../data/raw/' + audio_file)
        features = create_combined_features(y, sr)
        scaled_features = scale_features(features)
        all_features.append(scaled_features)

        species_idx = 7
        while(audio_file[species_idx].isdigit() == False):
            species_idx += 1
        species_idx -=1

        species = audio_file[7:species_idx]

        all_labels.append(species)
    return all_features, all_labels

def compare_before_after(before, after, sr, title1 = 'Before', title2 = 'After'):
    fig, ax = plt.subplots(2,1, figsize = (14,10))

    ax[0].set_title(title1)
    img1 = librosa.display.specshow(before, sr=sr, ax=ax[0], x_axis='time', y_axis='hz')
    plt.colorbar(img1, ax=ax[0], format='%+2.0f dB')

    ax[1].set_title(title2)
    img2 = librosa.display.specshow(after, sr=sr, ax=ax[1], x_axis='time', y_axis='hz')
    plt.colorbar(img2, ax=ax[1], format='%+2.0f dB')
    plt.style.use('default')

    plt.tight_layout()
    plt.show()

def spectral_substraction(noise_sample, y, sr, factor = 1, smoothing = None, return_audio = False):
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
    y_spectrum = librosa.stft(y)
    y_spectrum_db = librosa.amplitude_to_db(y_spectrum)
    y_spectrum_db[y_spectrum_db < cutoff] = -80

    phase = np.angle(y_spectrum)
    if return_audio:
        magnitude = librosa.db_to_amplitude(y_spectrum_db)
        complex_spectrum = magnitude * np.exp(1j * phase)
        # return librosa.istft(complex_spectrum)

    return y_spectrum_db

def examine_features(y, sr):
    # Extract features
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=8, n_fft=512, hop_length=512, fmin= 4000, fmax = 8000)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    rms = librosa.feature.rms(y=y)[0]

    # Create subplots
    plt.figure(figsize=(15, 10))

    # Plot each feature
    plt.subplot(3, 2, 1)
    plt.plot(centroid)
    plt.title('Spectral Centroid')

    plt.subplot(3, 2, 2)
    plt.plot(bandwidth)
    plt.title('Spectral Bandwidth')

    plt.subplot(3, 2, 3)
    plt.plot(rolloff)
    plt.title('Spectral Rolloff')

    plt.subplot(3, 2, 4)
    plt.plot(zcr)
    plt.title('Zero Crossing Rate')

    plt.subplot(3, 2, 5)
    plt.plot(rms)
    plt.title('RMS Energy')

    plt.tight_layout()
    plt.show()

def create_combined_features(y, sr):
    # Extract features
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=8, n_fft=512, hop_length=512, fmin= 4000, fmax = 8000)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    rms = librosa.feature.rms(y=y)[0]

    feature_dict = {
        'mfcc_means': np.mean(mfccs, axis=1),  # 13 values
        'mfcc_stds': np.std(mfccs, axis=1),    # 13 values
        'centroid_mean': np.mean(centroid),     # 1 value
        'centroid_std': np.std(centroid),       # 1 value
        'rolloff_mean': np.mean(rolloff),
        'rolloff_std': np.std(rolloff),
        'rms_mean': np.mean(rms),
        'rms_std': np.std(rms)
    }

    return feature_dict