# SignalScope Lab

A virtual signals-and-systems lab built with Streamlit. Upload a song or recording, choose an analysis, and explore the results interactively.

## Features

- **Time domain:** waveform statistics, time scaling, shifting, reversal, amplitude scaling, echo (convolution), autocorrelation and pitch
- **Frequency domain:** FFT magnitude, phase spectrum, STFT, spectrogram, Butterworth filters, spectral features
- **Music analysis:** instrument detection using the pretrained YAMNet model
- Play back and download processed audio as WAV

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
streamlit run signalscope_lab.py
```

Use Python 3.9 to 3.12 (TensorFlow compatibility). The first instrument detection run downloads the YAMNet model, so an internet connection is needed once.

## Supported formats

MP3, WAV, M4A and FLAC (decoded with FFmpeg through `imageio-ffmpeg`).

## Notes

Instrument detection is an estimate. YAMNet was trained on AudioSet and can miss or misclassify instruments in dense or heavily processed mixes.
