import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import librosa
import librosa.display
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk


# class that uses the librosa library to analyze the key that an mp3 is in
# arguments:
#     waveform: an mp3 file loaded by librosa, ideally separated out from any percussive sources
#     sr: sampling rate of the mp3, which can be obtained when the file is read with librosa
#     tstart and tend: the range in seconds of the file to be analyzed; default to the beginning and end of file if not specified
class Tonal_Fragment(object):
    def __init__(self, waveform, sr, tstart=None, tend=None):
        self.waveform = waveform
        self.sr = sr
        self.tstart = tstart
        self.tend = tend
        
        if self.tstart is not None:
            self.tstart = librosa.time_to_samples(self.tstart, sr=self.sr)
        if self.tend is not None:
            self.tend = librosa.time_to_samples(self.tend, sr=self.sr)
        self.y_segment = self.waveform[self.tstart:self.tend]
        self.chromograph = librosa.feature.chroma_cqt(y=self.y_segment, sr=self.sr, bins_per_octave=24)
        
        # chroma_vals is the amount of each pitch class present in this time interval
        self.chroma_vals = []
        for i in range(12):
            self.chroma_vals.append(np.sum(self.chromograph[i]))
        pitches = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        # dictionary relating pitch names to the associated intensity in the song
        self.keyfreqs = {pitches[i]: self.chroma_vals[i] for i in range(12)} 
        
        keys = [pitches[i] + ' major' for i in range(12)] + [pitches[i] + ' minor' for i in range(12)]

        # use of the Krumhansl-Schmuckler key-finding algorithm, which compares the chroma
        # data above to typical profiles of major and minor keys:
        maj_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        min_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

        # finds correlations between the amount of each pitch class in the time interval and the above profiles,
        # starting on each of the 12 pitches. then creates dict of the musical keys (major/minor) to the correlation
        self.min_key_corrs = []
        self.maj_key_corrs = []
        for i in range(12):
            key_test = [self.keyfreqs.get(pitches[(i + m)%12]) for m in range(12)]
            # correlation coefficients (strengths of correlation for each key)
            self.maj_key_corrs.append(round(np.corrcoef(maj_profile, key_test)[1,0], 3))
            self.min_key_corrs.append(round(np.corrcoef(min_profile, key_test)[1,0], 3))

        # names of all major and minor keys
        self.key_dict = {**{keys[i]: self.maj_key_corrs[i] for i in range(12)}, 
                         **{keys[i+12]: self.min_key_corrs[i] for i in range(12)}}
        
        # this attribute represents the key determined by the algorithm
        self.key = max(self.key_dict, key=self.key_dict.get)
        self.bestcorr = max(self.key_dict.values())
        
        # this attribute represents the second-best key determined by the algorithm,
        # if the correlation is close to that of the actual key determined
        self.altkey = None
        self.altbestcorr = None

        for key, corr in self.key_dict.items():
            if corr > self.bestcorr*0.9 and corr != self.bestcorr:
                self.altkey = key
                self.altbestcorr = corr
                
    # prints the relative prominence of each pitch class            
    def print_chroma(self):
        self.chroma_max = max(self.chroma_vals)
        for key, chrom in self.keyfreqs.items():
            print(key, '\t', f'{chrom/self.chroma_max:5.3f}')
                
    # prints the correlation coefficients associated with each major/minor key
    def corr_table(self):
        for key, corr in self.key_dict.items():
            print(key, '\t', f'{corr:6.3f}')
    
    # printout of the key determined by the algorithm; if another key is close, that key is mentioned
    def print_key(self):
        key_label.config(text=f'KEY: likely key --> {max(self.key_dict, key=self.key_dict.get)}, correlation --> {self.bestcorr}')
        if self.altkey is not None:
            key_label.config(text=f'KEY: likely key --> {max(self.key_dict, key=self.key_dict.get)}, correlation --> {self.bestcorr} | also possible ---> {self.altkey}, correlation --> {self.altbestcorr}')
    
    # generates image of a chromagram of the file, showing the intensity of each pitch class over time
    def chromagram_tk(self, title=None):
        C = librosa.feature.chroma_cqt(y=self.waveform, sr=self.sr, bins_per_octave=24)
    
        # Create a new figure
        fig = Figure(figsize=(9, 4))
        ax = fig.add_subplot(111)
        
        # Display the chromagram on the figure
        img = librosa.display.specshow(C, sr=self.sr, x_axis='time', y_axis='chroma', vmin=0, vmax=1, ax=ax)
        
        # Set the title
        if title is None:
            ax.set_title('Chromagram')
        else:
            ax.set_title(os.path.basename(title))
        
        # Add colorbar
        fig.colorbar(img, ax=ax)
        
        # Embed the figure in a Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=mainWindow)
        canvas.draw()
        canvas.get_tk_widget().place(x=0, y=150)
    
    # prints a chromagram of the file, showing the intensity of each pitch class over time
    def chromagram(self, title=None):
        C = librosa.feature.chroma_cqt(y=self.waveform, sr=self.sr, bins_per_octave=24)
        plt.figure(figsize=(12,4))
        librosa.display.specshow(C, sr=self.sr, x_axis='time', y_axis='chroma', vmin=0, vmax=1)
        if title is None:
            plt.title('Chromagram')
        else:
            plt.title(title)
        plt.colorbar()
        plt.tight_layout()
        plt.show()

def import_audio_file():
    progress_bar['value'] = 0
    mainWindow.update_idletasks()

    filetypes = [('Audio Files', '*.mp3;*.wav;')]
    file_path = filedialog.askopenfilename(title='Open an audio file', filetypes=filetypes)
    if file_path:
        file_selected_name.config(text=f'Audio File Selected: {os.path.basename(file_path)}')
        
        progress_bar['value'] = 20
        mainWindow.update_idletasks()
        
        analyze_audio_file(file_path=file_path)

        progress_bar['value'] = 100
        mainWindow.update_idletasks()

def analyze_audio_file(file_path):
    y, sr = librosa.load(file_path)
    y_harmonic, y_percussive = librosa.effects.hpss(y)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
    tempo_label.config(text=f'BPM: {tempo}')

    track = Tonal_Fragment(y_harmonic, sr)
    track.print_key()

    progress_bar['value'] = 50
    mainWindow.update_idletasks()

    track.chromagram_tk(title=file_path)

    detail_button = tk.Button(master=mainWindow, text='Details Chart', command=track.chromagram, background='#AA4F4F', foreground='#FFFFFF')
    detail_button.place(x=700, y=560)


mainWindow = tk.Tk()
w = 800
h = 600
ws = mainWindow.winfo_screenwidth()
hs = mainWindow.winfo_screenheight()
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)
mainWindow.geometry('%dx%d+%d+%d' % (w, h, x, y))
mainWindow.resizable(width=False, height=False)
mainWindow.title('PyMusic Analizer')
mainWindow.configure(background='#ffffff')


import_button = tk.Button(master=mainWindow, text='Select Audio File', command=import_audio_file, background='#AA4F4F', foreground='#FFFFFF')
import_button.place(x=20, y=20)

progress_bar = ttk.Progressbar(master=mainWindow, orient='horizontal', mode='determinate', length=300)
progress_bar.place(x=150, y=23)

file_selected_name = tk.Label(master=mainWindow, text='Audio File Selected: ', background='#FFFFFF', foreground='#265D80')
file_selected_name.place(x=20, y=60)

tempo_label = tk.Label(master=mainWindow, text='BPM: ', background='#FFFFFF', foreground='#265D80')
tempo_label.place(x=20, y=100)
key_label = tk.Label(master=mainWindow, text='KEY: ', background='#FFFFFF', foreground='#265D80')
key_label.place(x=170, y=100)


mainWindow.mainloop()