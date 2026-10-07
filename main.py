import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import stft



file_path = r"C:\College stuff\SY\Signals and systems\Virtual lab\example.wav"

fs, signal = wavfile.read(file_path)

print("Sampling frequency:", fs, "Hz")
print("Number of samples:", len(signal))
print("Duration:", len(signal) / fs, "seconds")



if signal.ndim == 2:
    signal = signal.mean(axis=1)










# Convert to floating point
signal = signal.astype(float)

# Normalize amplitude
signal = signal / np.max(np.abs(signal))

# ==========================================
# 3. Create time axis
# ==========================================

t = np.arange(len(signal)) / fs

# ==========================================
# 4. TIME DOMAIN
# ==========================================

plt.figure(figsize=(12, 4))

plt.plot(t, signal)

plt.title("Audio Signal - Time Domain")
plt.xlabel("Time (seconds)")
plt.ylabel("Amplitude")
plt.grid()

plt.tight_layout()
plt.show()

# ==========================================
# 5. STFT
# ==========================================

frequencies_stft, times_stft, Zxx = stft(
    signal,
    fs=fs,
    nperseg=1024
)

stft_magnitude = np.abs(Zxx)

# Convert magnitude to decibels
stft_db = 20 * np.log10(stft_magnitude + 1e-10)

# ==========================================
# 6. STFT SPECTROGRAM
# ==========================================

plt.figure(figsize=(12, 6))

plt.pcolormesh(
    times_stft,
    frequencies_stft,
    stft_db,
    shading="gouraud"
)

plt.colorbar(label="Magnitude (dB)")

plt.title("STFT Spectrogram")
plt.xlabel("Time (seconds)")
plt.ylabel("Frequency (Hz)")

# Zoom into the useful frequency range
plt.ylim(0, 2000)

plt.tight_layout()
plt.show()

# ==========================================
# 7. FOURIER TRANSFORM
# ==========================================

N = len(signal)

fft_result = np.fft.rfft(signal)

frequencies_fft = np.fft.rfftfreq(N, 1 / fs)

fft_magnitude = np.abs(fft_result) / N

# ==========================================
# 8. FREQUENCY SPECTRUM
# ==========================================

plt.figure(figsize=(12, 5))

plt.plot(
    frequencies_fft,
    fft_magnitude
)

plt.title("Fourier Transform - Frequency Spectrum")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")

plt.xlim(0, 2000)

plt.grid()

plt.tight_layout()
plt.show()