from keyfinder import Tonal_Fragment as TF
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display


audio_path = 'This Wandering Day.mp3'
y, sr = librosa.load(audio_path)
y_harmonic, y_percussive = librosa.effects.hpss(y)

onset_env = librosa.onset.onset_strength(y=y, sr=sr)
tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
print(tempo)

track = TF(y_harmonic, sr)
track.chromagram(audio_path)

track.print_key()