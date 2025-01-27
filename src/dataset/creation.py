import numpy as np
import librosa
import librosa.feature
from sklearn.preprocessing import StandardScaler

#TODO: Refactor to using Call DataClass
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

