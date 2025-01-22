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

from src import *
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
#%%
api = XenoCantoAPI()

recordings = api.search_api("Turdus merula", cnt="Germany")

api.download_recordings(recordings[:15])


#%%
y, sr = librosa.load(RAW_DATA_DIR /
                     '842671_Turdus_merula_2023-11-02_Germany.mp3', sr = 22050)
D = librosa.stft(y)

D_db = librosa.amplitude_to_db(D)

plt.figure(figsize = (14, 5))
librosa.display.specshow(D_db, sr = sr,
                         x_axis='time', y_axis='hz')
plt.show()
#%%

threshold = -20

D_db_clean = D_db.copy()
D_db_clean[D_db_clean < threshold] = -80

plt.figure(figsize = (14, 10))

plt.subplot(2, 1, 1)
librosa.display.specshow(D_db, sr = sr, x_axis='time', y_axis='hz')
plt.colorbar(format='%+2.0f dB')
plt.title('Before reduction')
plt.subplot(2, 1, 2)
librosa.display.specshow(D_db_clean, sr = sr, x_axis='time', y_axis='hz')
plt.colorbar(format='%+2.0f dB')
plt.title('After reduction')
plt.show()