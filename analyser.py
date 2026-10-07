import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy import signal
from scipy.io import wavfile
import imageio_ffmpeg
import subprocess, tempfile, html, io, os

st.set_page_config(page_title="SignalScope Lab", page_icon="📡", layout="wide",
                   initial_sidebar_state="collapsed")

INK, PANEL, EDGE, TEXT, MUTED = "#0a0e14", "#111823", "#1f2a3a", "#e6edf6", "#8494ab"
TEAL, AMBER, VIOLET = "#3ee6c4", "#ffb454", "#8b7cff"
CMAP = LinearSegmentedColormap.from_list(
    "signalscope", ["#0a0e14", "#1b2a6b", "#6a3fd1", "#e2568b", "#ffb454", "#fff3d6"])

st.markdown("<style>:root{--ink:%s;--panel:%s;--edge:%s;--text:%s;--muted:%s;--teal:%s;--amber:%s}</style>"
            % (INK, PANEL, EDGE, TEXT, MUTED, TEAL, AMBER), unsafe_allow_html=True)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@500&display=swap');
html, body, [class*="css"], .stApp { font-family:'IBM Plex Sans',Arial,sans-serif; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility:hidden; height:0; }
.stApp { color:var(--text);
  background: linear-gradient(rgba(62,230,196,.035) 1px,transparent 1px) 0 0/48px 48px,
              linear-gradient(90deg,rgba(62,230,196,.035) 1px,transparent 1px) 0 0/48px 48px,
              radial-gradient(ellipse at 80% -10%,rgba(62,230,196,.10),transparent 45%), var(--ink); }
.block-container { max-width:1200px; padding:2.5rem 1.5rem 4rem; }
.hero { display:flex; align-items:center; justify-content:space-between; gap:32px; padding:38px 44px;
  border-radius:18px; background:linear-gradient(120deg,#0f1826,#0c1320); border:1px solid var(--edge); margin-bottom:34px; }
.hero-title { font-family:'Space Grotesk',sans-serif; font-size:50px; font-weight:700; letter-spacing:-1.5px; line-height:1; margin-bottom:12px; }
.hero-subtitle { color:var(--muted); font-size:17px; max-width:460px; line-height:1.55; margin-bottom:20px; }
.badge { display:inline-block; padding:6px 13px; margin:0 8px 6px 0; border-radius:6px;
  background:rgba(62,230,196,.07); border:1px solid rgba(62,230,196,.25); color:var(--teal); font-size:13px; font-weight:500; }
.hero-art { flex:0 0 auto; width:360px; max-width:45%; }
.hero-art svg { width:100%; height:auto; display:block; }
.trace { stroke-dasharray:1500; stroke-dashoffset:1500; animation:draw 2.4s ease-out forwards; }
@keyframes draw { to { stroke-dashoffset:0; } }
@media (prefers-reduced-motion:reduce) { .trace { animation:none; stroke-dashoffset:0; } }
@media (max-width:760px) { .hero { flex-direction:column; align-items:flex-start; padding:26px; } .hero-art { width:100%; max-width:100%; } .hero-title { font-size:38px; } }
.section-header { margin:42px 0 16px; padding-left:16px; border-left:3px solid var(--accent,var(--teal)); }
.section-title { font-family:'Space Grotesk',sans-serif; font-size:25px; font-weight:700; letter-spacing:-.5px; line-height:1.2; }
.section-description { color:var(--muted); font-size:15px; margin-top:4px; }
.info-card { padding:16px 20px; border-radius:12px; background:var(--panel); border:1px solid var(--edge); margin-bottom:12px; }
.info-title { font-size:13px; color:var(--muted); margin-bottom:6px; }
.info-value { font-family:'IBM Plex Mono',monospace; font-size:19px; font-weight:500; word-break:break-all; }
.info-value.accent { color:var(--teal); }
.bench { padding:18px 22px; border-radius:14px; background:var(--panel); border:1px solid var(--edge); margin-bottom:16px; }
.bench b { font-family:'Space Grotesk',sans-serif; font-size:20px; }
.bench span { display:block; color:var(--muted); font-size:14px; margin-top:4px; line-height:1.5; }
div[role="radiogroup"] { gap:10px; }
div[role="radiogroup"] label { background:var(--panel); border:1px solid var(--edge); border-radius:10px; padding:10px 20px; }
div[role="radiogroup"] label:has(input:checked) { border-color:var(--teal); background:rgba(62,230,196,.08); }
[data-testid="stFileUploaderDropzone"] { background:var(--panel); border:1.5px dashed rgba(62,230,196,.35); border-radius:14px; padding:26px; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:var(--teal); }
[data-testid="stFileUploaderDropzone"] button { background:transparent; color:var(--teal); border:1px solid var(--teal); border-radius:8px; }
[data-testid="stAlert"], [data-testid="stExpander"] { background:var(--panel); border:1px solid var(--edge); border-radius:12px; }
[data-baseweb="slider"] [role="slider"] { background-color:var(--teal) !important; box-shadow:0 0 0 5px rgba(62,230,196,.18) !important; }
[data-testid="stDownloadButton"] button { background:transparent; color:var(--amber); border:1px solid var(--amber); border-radius:8px; }
audio { width:100%; border-radius:12px; filter:invert(.92) hue-rotate(140deg) saturate(.7); }
[data-testid="stImage"] img { border-radius:14px; border:1px solid var(--edge); }
.footer { text-align:center; color:#56647d; font-size:13px; margin-top:64px; padding-top:24px; border-top:1px solid var(--edge); }
</style>
""", unsafe_allow_html=True)



def section(title, desc, accent=TEAL):
    st.markdown(f'<div class="section-header" style="--accent:{accent}"><div class="section-title">{title}</div>'
                f'<div class="section-description">{desc}</div></div>', unsafe_allow_html=True)


def info_card(label, value, accent=False):
    cls = "info-value accent" if accent else "info-value"
    st.markdown(f'<div class="info-card"><div class="info-title">{label}</div>'
                f'<div class="{cls}">{html.escape(str(value))}</div></div>', unsafe_allow_html=True)


def stats(d, per_row=3):
    items = list(d.items())
    for i in range(0, len(items), per_row):
        for col, (k, v) in zip(st.columns(per_row), items[i:i + per_row]):
            with col:
                info_card(k, v, accent=True)


def style(ax, title, xl, yl):
    ax.set_facecolor(PANEL)
    ax.set_title(title, fontsize=13, fontweight="bold", color=TEXT, pad=10, loc="left")
    ax.set_xlabel(xl, color=MUTED, labelpad=6)
    ax.set_ylabel(yl, color=MUTED, labelpad=6)
    ax.tick_params(colors=MUTED, length=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(EDGE)
    ax.grid(True, color=EDGE, alpha=.7, linewidth=.6)
    ax.set_axisbelow(True)


def stacked(n, h=3.0):
    fig, axs = plt.subplots(n, 1, figsize=(11, h * n))
    fig.patch.set_facecolor(PANEL)
    return fig, np.atleast_1d(axs)


def show(fig):
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def decim(t, y, n=4000):
    """Min/max decimation so long signals plot fast without losing peaks."""
    if len(y) <= 2 * n:
        return t, y
    k = len(y) // n
    m = k * n
    r = y[:m].reshape(n, k)
    return np.repeat(t[:m:k], 2), np.column_stack([r.min(1), r.max(1)]).ravel()


def draw(ax, series, title, xl="Time (s)", yl="Amplitude"):
    """series: list of (t, y, color, label). One series is filled, several are overlaid."""
    style(ax, title, xl, yl)
    m = 1e-9
    for t, y, c, lab in series:
        tt, yy = decim(t, y)
        ax.plot(tt, yy, color=c, lw=.8, label=lab)
        if len(series) == 1:
            ax.fill_between(tt, yy, color=c, alpha=.15, lw=0)
        m = max(m, np.max(np.abs(y)))
    ax.set_ylim(-m * 1.08, m * 1.08)
    ax.set_xlim(min(s[0][0] for s in series), max(s[0][-1] for s in series))
    ax.axhline(0, color=MUTED, lw=.5, alpha=.6)
    if len(series) > 1:
        ax.legend(facecolor=PANEL, edgecolor=EDGE, labelcolor=TEXT, loc="upper right")


def playback(y, name):
    y = np.asarray(y, dtype=np.float64)
    if y.size < 2:
        return
    y = y / max(1.0, np.max(np.abs(y)))
    st.audio(y.astype(np.float32), sample_rate=SR)
    buf = io.BytesIO()
    wavfile.write(buf, SR, (y * 32767).astype(np.int16))
    st.download_button("Download WAV", buf.getvalue(), f"{name}.wav", "audio/wav")


@st.cache_data(show_spinner=False)
def decode_audio(data, ext):
    in_p = out_p = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            f.write(data)
            in_p = f.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            out_p = f.name
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", in_p, "-vn", "-ac", "1",
               "-ar", "44100", "-c:a", "pcm_s16le", out_p]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode("utf-8", errors="ignore"))
        sr, x = wavfile.read(out_p)
        return sr, x.astype(np.float64)
    finally:
        for p in (in_p, out_p):
            if p:
                try:
                    os.remove(p)
                except OSError:
                    pass


def spectrum(sig, win="hann"):
    w = signal.get_window(win, len(sig))
    X = np.fft.rfft(sig * w)
    return np.fft.rfftfreq(len(sig), 1 / SR), X, np.abs(X) / np.sum(w) * 2


def fmax_slider(key="fmax"):
    nyq = int(SR // 2)
    return st.slider("Max frequency (Hz)", 100, nyq, min(10000, nyq), 100, key=key)


def db(v):
    return 20 * np.log10(np.abs(v) + 1e-10)



xs_ = np.linspace(0, 360, 180)
ys_ = 70 - 28 * np.sin(xs_ / 14) - 14 * np.sin(xs_ / 5.3)
path = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in zip(xs_, ys_))
st.markdown(f"""
<div class="hero"><div>
  <div class="hero-title">📡 SignalScope Lab</div>
  <div class="hero-subtitle">A virtual signals and systems lab. Upload a recording, pick an experiment, change the parameters and watch the signal respond.</div>
  <span class="badge">Time domain</span><span class="badge">Fourier transform</span>
  <span class="badge">Phase</span><span class="badge">STFT</span><span class="badge">Spectrogram</span><span class="badge">Filters</span>
</div><div class="hero-art"><svg viewBox="0 0 360 140" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <g stroke="{EDGE}"><line x1="0" y1="70" x2="360" y2="70"/><line x1="90" y1="0" x2="90" y2="140" opacity=".5"/>
  <line x1="180" y1="0" x2="180" y2="140" opacity=".5"/><line x1="270" y1="0" x2="270" y2="140" opacity=".5"/></g>
  <path class="trace" d="{path}" fill="none" stroke="{TEAL}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
</svg></div></div>
""", unsafe_allow_html=True)

FOOTER = '<div class="footer">SignalScope Lab: time domain, Fourier transform, phase, STFT, spectrogram and filtering</div>'


section("Upload audio", "Every experiment in this lab runs on the file you add here.")
uploaded = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "flac"],
                            help="Supported formats: MP3, WAV, M4A and FLAC")
if uploaded is None:
    st.info("🎵 Upload an MP3, WAV, M4A or FLAC file to open the lab.")
    st.markdown(FOOTER, unsafe_allow_html=True)
    st.stop()

input_bytes = uploaded.getvalue()
try:
    with st.spinner("Decoding audio..."):
        SR, audio = decode_audio(input_bytes, os.path.splitext(uploaded.name)[1].lower())
except Exception as e:
    st.error(f"Could not decode this file. {str(e)[-300:]}")
    st.stop()

if audio.size == 0:
    st.error("The uploaded audio file contains no usable audio data.")
    st.stop()
peak = np.max(np.abs(audio))
if peak > 0:
    audio = audio / peak
duration = len(audio) / SR


section("Your signal", "Properties, playback and the segment every experiment will use.")
c1, c2, c3 = st.columns(3)
with c1:
    info_card("File", uploaded.name)
with c2:
    info_card("Sampling frequency", f"{SR:,} Hz", True)
with c3:
    info_card("Duration", f"{duration:.2f} s", True)
st.audio(input_bytes, format=uploaded.type)

if duration <= 0.1:
    t_start, t_end = 0.0, duration
else:
    t_start, t_end = st.slider("Analysis segment", 0.0, float(duration), (0.0, float(duration)),
                               step=0.01, format="%.2f s")
x = audio[int(t_start * SR):int(t_end * SR)]
N = len(x)
if N < 64:
    st.warning("Select a longer segment (at least 64 samples) to run experiments.")
    st.stop()
dur = N / SR
T = np.arange(N) / SR



def exp_waveform():
    with ctrl:
        env = st.checkbox("Overlay Hilbert envelope", True)
    with out:
        fig, (ax,) = stacked(1, 4.2)
        series = [(T + t_start, x, TEAL, "x(t)")]
        if env:
            series.append((T + t_start, np.abs(signal.hilbert(x)), AMBER, "Envelope"))
        draw(ax, series, "Audio waveform")
        show(fig)
        rms = np.sqrt(np.mean(x ** 2))
        stats({"Peak": f"{np.max(np.abs(x)):.3f}", "RMS": f"{rms:.3f}",
               "Crest factor": f"{np.max(np.abs(x)) / (rms + 1e-12):.2f}",
               "Zero crossings/s": f"{np.sum(np.diff(np.signbit(x))) / dur:,.0f}",
               "DC offset": f"{np.mean(x):+.4f}", "Energy": f"{np.sum(x ** 2):,.1f}"})


def exp_scaling():
    with ctrl:
        a = st.slider("Scaling factor a", 0.25, 4.0, 2.0, 0.05)
        st.caption("a > 1 compresses the signal in time. a < 1 expands it.")
    n2 = max(2, int(N / a))
    t2 = np.arange(n2) / SR
    y = np.interp(t2 * a, T, x)
    with out:
        fig, axs = stacked(2)
        draw(axs[0], [(T, x, TEAL, "")], "Original x(t)")
        kind = "compressed" if a > 1 else "expanded" if a < 1 else "unchanged"
        draw(axs[1], [(t2, y, AMBER, "")], f"Time-scaled y(t) = x({a:g}t), {kind}")
        show(fig)
        stats({"Original length": f"{dur:.2f} s", "New length": f"{n2 / SR:.2f} s", "Pitch factor": f"x{a:g}"})
        playback(y, "time_scaled")


def exp_shift():
    lim = float(min(dur, 5.0))
    with ctrl:
        s = st.slider("Shift (s)", -lim, lim, min(0.5, lim / 4), 0.01)
        circ = st.checkbox("Circular shift (wrap around)", False)
        st.caption("Positive shift delays the signal. Negative shift advances it.")
    k = int(round(s * SR))
    if circ:
        y = np.roll(x, k)
    else:
        y = np.zeros(N)
        if k >= 0:
            y[k:] = x[:N - k]
        else:
            y[:N + k] = x[-k:]
    with out:
        fig, (ax,) = stacked(1, 4.4)
        draw(ax, [(T, x, MUTED, "x(t)"), (T, y, AMBER, f"y(t) = x(t - {s:g})")],
             "Delayed signal" if s >= 0 else "Advanced signal")
        show(fig)
        stats({"Shift": f"{s:+.2f} s", "Samples": f"{k:+,}", "Type": "Circular" if circ else "Zero-padded"})
        playback(y, "time_shifted")


def exp_reverse():
    y = x[::-1]
    with out:
        fig, (ax,) = stacked(1, 4.4)
        draw(ax, [(T, x, MUTED, "x(t)"), (T, y, AMBER, "y(t) = x(-t)")], "Time reversal")
        show(fig)
        playback(y, "time_reversed")


def exp_amplitude():
    with ctrl:
        g = st.slider("Gain (dB)", -30.0, 30.0, 6.0, 0.5)
        dc = st.slider("DC offset", -0.5, 0.5, 0.0, 0.01)
        clip = st.checkbox("Hard clip at +/-1 (distortion)", False)
    y = 10 ** (g / 20) * x + dc
    if clip:
        y = np.clip(y, -1, 1)
    with out:
        fig, (ax,) = stacked(1, 4.4)
        draw(ax, [(T, x, MUTED, "x(t)"), (T, y, AMBER, "y(t) = A x(t) + c")], "Amplitude scaling")
        show(fig)
        stats({"Gain": f"x{10 ** (g / 20):.2f}", "New peak": f"{np.max(np.abs(y)):.3f}",
               "Clipped samples": f"{np.mean(np.abs(y) >= 1) * 100:.1f} %"})
        playback(y, "amplitude_scaled")


def exp_echo():
    with ctrl:
        d = st.slider("Echo delay (ms)", 20, 1000, 250, 10)
        gain = st.slider("Echo gain", 0.0, 0.95, 0.5, 0.05)
        reps = st.slider("Repeats", 1, 8, 3)
    D = int(d * SR / 1000)
    h = np.zeros(D * reps + 1)
    h[0] = 1
    for i in range(1, reps + 1):
        h[i * D] = gain ** i
    y = signal.fftconvolve(x, h)
    with out:
        fig, axs = stacked(2, 3.0)
        style(axs[0], "Impulse response h(t)", "Time (s)", "Amplitude")
        th = np.arange(len(h)) / SR
        axs[0].vlines(th[h > 0], 0, h[h > 0], color=VIOLET, lw=2)
        axs[0].set_ylim(0, 1.15)
        draw(axs[1], [(np.arange(len(y)) / SR, y, AMBER, "y = x * h"), (T, x, MUTED, "x(t)")], "Convolution with echo")
        show(fig)
        playback(y, "echo")


def exp_autocorr():
    xs = x[:min(N, 4 * SR)]
    xs = xs - xs.mean()
    r = signal.fftconvolve(xs, xs[::-1])[len(xs) - 1:]
    r = r / (r[0] + 1e-12)
    with ctrl:
        ml = st.slider("Max lag (ms)", 5, 50, 30)
    lo, hi = int(SR / 1000), min(int(SR / 50), len(r) - 1)
    f0 = "No clear pitch"
    if hi > lo:
        k = lo + int(np.argmax(r[lo:hi]))
        if r[k] > 0.3:
            f0 = f"{SR / k:,.1f} Hz"
    L = min(len(r), int(ml * SR / 1000))
    with out:
        fig, (ax,) = stacked(1, 4.2)
        draw(ax, [(np.arange(L) / SR * 1000, r[:L], VIOLET, "")], "Autocorrelation", "Lag (ms)", "Normalized R(lag)")
        show(fig)
        stats({"Estimated pitch": f0, "Analysed": f"{len(xs) / SR:.2f} s"}, 2)



WINDOWS = ["boxcar", "hann", "hamming", "blackman"]


def exp_fft():
    with ctrl:
        win = st.selectbox("Window", WINDOWS, 1)
        scale = st.radio("Magnitude scale", ["Linear", "dB"], horizontal=True)
        fmax = fmax_slider()
        logf = st.checkbox("Log frequency axis", False)
        npk = st.slider("Peaks to list", 1, 10, 5)
    f, X, mag = spectrum(x, win)
    yv = mag if scale == "Linear" else db(mag)
    idx, _ = signal.find_peaks(mag, height=mag.max() * 0.02, distance=max(1, int(20 / (SR / N))))
    top = idx[np.argsort(mag[idx])[::-1][:npk]]
    with out:
        fig, (ax,) = stacked(1, 4.6)
        style(ax, "Magnitude spectrum", "Frequency (Hz)", "Magnitude" if scale == "Linear" else "Magnitude (dB)")
        ax.plot(f, yv, color=AMBER, lw=1)
        if scale == "Linear":
            ax.fill_between(f, yv, color=AMBER, alpha=.18, lw=0)
            ax.set_ylim(bottom=0)
        ax.plot(f[top], yv[top], "o", color=TEAL, ms=6)
        if logf:
            ax.set_xscale("log")
            ax.set_xlim(20, fmax)
        else:
            ax.set_xlim(0, fmax)
        show(fig)
        if len(top):
            st.dataframe({"Frequency (Hz)": np.round(f[top], 1), "Magnitude": np.round(mag[top], 5),
                          "Level (dB)": np.round(db(mag[top]), 1)}, use_container_width=True, hide_index=True)


def exp_phase():
    with ctrl:
        win = st.selectbox("Window", WINDOWS, 1, key="pw")
        unwrap = st.checkbox("Unwrap phase", False)
        deg = st.radio("Units", ["Radians", "Degrees"], horizontal=True)
        thr = st.slider("Hide bins below (dB from peak)", -100, -10, -40)
        fmax = fmax_slider("pf")
    f, X, mag = spectrum(x, win)
    ph = np.unwrap(np.angle(X)) if unwrap else np.angle(X)
    if deg == "Degrees":
        ph = np.degrees(ph)
    ph = np.where(db(mag / mag.max()) < thr, np.nan, ph)
    with out:
        fig, axs = stacked(2, 3.2)
        style(axs[0], "Magnitude (dB)", "Frequency (Hz)", "dB")
        axs[0].plot(f, db(mag), color=AMBER, lw=.9)
        style(axs[1], "Phase spectrum", "Frequency (Hz)", "Phase (rad)" if deg == "Radians" else "Phase (deg)")
        axs[1].plot(f, ph, color=VIOLET, lw=0, marker=".", ms=2)
        for a in axs:
            a.set_xlim(0, fmax)
        show(fig)
        st.caption("Phase is only meaningful where the magnitude is significant, so weak bins are hidden.")


def frames_params(prefix):
    nper = st.select_slider("Window length (samples)", [256, 512, 1024, 2048, 4096], 2048, key=prefix + "n")
    ov = st.select_slider("Overlap", [0, 25, 50, 75], 50, format_func=lambda v: f"{v} %", key=prefix + "o")
    win = st.selectbox("Window", WINDOWS[1:], key=prefix + "w")
    nper = min(nper, N)
    hop = max(1, int(nper * (1 - ov / 100)), N // 3000)
    return nper, hop, win


def exp_stft():
    with ctrl:
        nper, hop, win = frames_params("s")
        what = st.radio("Show", ["Magnitude", "Phase"], horizontal=True)
        dr = st.slider("Dynamic range (dB)", 20, 120, 80)
        fmax = fmax_slider("sf")
    w = signal.get_window(win, nper)
    fr = np.lib.stride_tricks.sliding_window_view(x, nper)[::hop]
    S = np.fft.rfft(fr * w, axis=1).T
    f = np.fft.rfftfreq(nper, 1 / SR)
    tt = t_start + (np.arange(fr.shape[0]) * hop + nper // 2) / SR
    with out:
        fig, (ax,) = stacked(1, 5.2)
        style(ax, f"STFT {what.lower()}", "Time (s)", "Frequency (Hz)")
        ax.grid(False)
        if what == "Magnitude":
            d = db(S)
            mesh = ax.pcolormesh(tt, f, d, cmap=CMAP, vmin=d.max() - dr, vmax=d.max(), shading="auto")
            lab = "Magnitude (dB)"
        else:
            mesh = ax.pcolormesh(tt, f, np.angle(S), cmap="twilight", vmin=-np.pi, vmax=np.pi, shading="auto")
            lab = "Phase (rad)"
        ax.set_ylim(0, fmax)
        cb = fig.colorbar(mesh, ax=ax, pad=.02)
        cb.set_label(lab, color=MUTED)
        cb.ax.tick_params(colors=MUTED, length=0)
        cb.outline.set_edgecolor(EDGE)
        show(fig)
        stats({"Frequency resolution": f"{SR / nper:.1f} Hz", "Time step": f"{hop / SR * 1000:.1f} ms",
               "Frames": f"{fr.shape[0]:,}"})
        tsel = st.slider("Inspect one frame at time (s)", float(tt[0]), float(tt[-1]), float(tt[0]), key="insp") \
            if len(tt) > 1 else tt[0]
        j = int(np.argmin(np.abs(tt - tsel)))
        fig2, (ax2,) = stacked(1, 3.0)
        style(ax2, f"Spectrum of the frame at {tt[j]:.2f} s", "Frequency (Hz)", "dB")
        ax2.plot(f, db(S[:, j]), color=TEAL, lw=1)
        ax2.set_xlim(0, fmax)
        show(fig2)


def exp_spectrogram():
    with ctrl:
        nper, hop, win = frames_params("g")
        scaling = st.radio("Scaling", ["density", "spectrum"], horizontal=True)
        cm = st.selectbox("Colormap", ["signalscope", "magma", "viridis", "inferno"])
        logf = st.checkbox("Log frequency axis", False)
        dr = st.slider("Dynamic range (dB)", 20, 120, 80, key="gdr")
        fmax = fmax_slider("gf")
    f, tt, Sxx = signal.spectrogram(x, SR, window=win, nperseg=nper, noverlap=nper - min(hop, nper - 1),
                                    scaling=scaling, mode="psd")
    d = 10 * np.log10(Sxx + 1e-12)
    with out:
        fig, (ax,) = stacked(1, 5.2)
        style(ax, "Spectrogram (power)", "Time (s)", "Frequency (Hz)")
        ax.grid(False)
        mesh = ax.pcolormesh(tt + t_start, f, d, cmap=CMAP if cm == "signalscope" else cm,
                             vmin=d.max() - dr, vmax=d.max(), shading="auto")
        if logf:
            ax.set_yscale("log")
            ax.set_ylim(20, fmax)
        else:
            ax.set_ylim(0, fmax)
        cb = fig.colorbar(mesh, ax=ax, pad=.02)
        cb.set_label("Power (dB)", color=MUTED)
        cb.ax.tick_params(colors=MUTED, length=0)
        cb.outline.set_edgecolor(EDGE)
        show(fig)
        st.caption("A longer window gives finer frequency detail but blurs timing. A shorter window does the opposite.")


def exp_filter():
    nyq = int(SR // 2)
    with ctrl:
        kind = st.selectbox("Filter type", ["Low-pass", "High-pass", "Band-pass", "Band-stop"])
        order = st.slider("Order", 1, 10, 4)
        if kind in ("Low-pass", "High-pass"):
            fc = st.slider("Cutoff (Hz)", 20, nyq - 100, 2000, 10)
            wn, marks = fc, [fc]
        else:
            lo, hi = st.slider("Band edges (Hz)", 20, nyq - 100, (300, 3000), 10)
            if hi - lo < 10:
                st.warning("Make the band at least 10 Hz wide.")
                return
            wn, marks = [lo, hi], [lo, hi]
        zp = st.checkbox("Zero-phase (forward and backward)", True)
        fmax = fmax_slider("ff")
    btype = {"Low-pass": "lowpass", "High-pass": "highpass", "Band-pass": "bandpass", "Band-stop": "bandstop"}[kind]
    sos = signal.butter(order, wn, btype, fs=SR, output="sos")
    y = signal.sosfiltfilt(sos, x) if zp and N > 200 else signal.sosfilt(sos, x)
    w, h = signal.sosfreqz(sos, worN=4096, fs=SR)
    f, _, m0 = spectrum(x)
    _, _, m1 = spectrum(y)
    with out:
        fig, axs = stacked(2, 3.2)
        style(axs[0], "Filter frequency response", "Frequency (Hz)", "Gain (dB)")
        axs[0].plot(w, db(h), color=VIOLET, lw=1.4)
        axs[0].set_ylim(-80, 5)
        for mk in marks:
            axs[0].axvline(mk, color=MUTED, ls="--", lw=.8)
        style(axs[1], "Spectrum before and after", "Frequency (Hz)", "Magnitude (dB)")
        axs[1].plot(f, db(m0), color=MUTED, lw=.8, label="Input")
        axs[1].plot(f, db(m1), color=AMBER, lw=.9, label="Filtered")
        axs[1].legend(facecolor=PANEL, edgecolor=EDGE, labelcolor=TEXT)
        for a in axs:
            a.set_xlim(0, fmax)
        show(fig)
        playback(y, "filtered")


def exp_features():
    with ctrl:
        pct = st.slider("Roll-off percentage", 50, 99, 85)
        fmax = fmax_slider("xf")
    f, _, mag = spectrum(x)
    P = mag ** 2 + 1e-20
    cen = np.sum(f * P) / np.sum(P)
    bw = np.sqrt(np.sum((f - cen) ** 2 * P) / np.sum(P))
    cum = np.cumsum(P) / np.sum(P)
    roll = f[min(np.searchsorted(cum, pct / 100), len(f) - 1)]
    flat = np.exp(np.mean(np.log(P))) / np.mean(P)
    with out:
        fig, axs = stacked(2, 3.0)
        style(axs[0], "Spectrum with centroid and roll-off", "Frequency (Hz)", "Magnitude (dB)")
        axs[0].plot(f, db(mag), color=AMBER, lw=.9)
        axs[0].axvline(cen, color=TEAL, lw=1.2, label="Centroid")
        axs[0].axvline(roll, color=VIOLET, lw=1.2, label=f"{pct}% roll-off")
        axs[0].legend(facecolor=PANEL, edgecolor=EDGE, labelcolor=TEXT)
        style(axs[1], "Cumulative energy", "Frequency (Hz)", "Fraction of energy")
        axs[1].plot(f, cum, color=VIOLET, lw=1.4)
        for a in axs:
            a.set_xlim(0, fmax)
        show(fig)
        stats({"Spectral centroid": f"{cen:,.0f} Hz", "Bandwidth": f"{bw:,.0f} Hz",
               f"{pct}% roll-off": f"{roll:,.0f} Hz", "Flatness": f"{flat:.4f}",
               "Dominant frequency": f"{f[1 + int(np.argmax(mag[1:]))]:,.1f} Hz"})



FAMILIES = {
    "Vocals": ["Singing", "Male singing", "Female singing", "Child singing", "Choir", "Rapping", "Humming",
               "Synthetic singing", "Yodeling"],
    "Guitar": ["Guitar", "Acoustic guitar", "Electric guitar", "Steel guitar, slide guitar", "Strum",
               "Tapping (guitar technique)"],
    "Bass guitar": ["Bass guitar"],
    "Piano and keys": ["Piano", "Electric piano", "Keyboard (musical)", "Organ", "Electronic organ",
                       "Hammond organ", "Harpsichord"],
    "Synthesizer": ["Synthesizer", "Sampler", "Theremin"],
    "Drums": ["Drum kit", "Drum machine", "Drum", "Snare drum", "Bass drum", "Rimshot", "Drum roll",
              "Timpani", "Tabla"],
    "Cymbals and hi-hat": ["Cymbal", "Hi-hat"],
    "Other percussion": ["Percussion", "Tambourine", "Maraca", "Rattle (instrument)", "Wood block", "Gong",
                         "Tubular bells", "Mallet percussion", "Marimba, xylophone", "Glockenspiel",
                         "Vibraphone", "Steelpan"],
    "Bowed strings": ["Violin, fiddle", "Cello", "Double bass", "Bowed string instrument", "String section",
                      "Pizzicato"],
    "Harp and plucked strings": ["Harp", "Banjo", "Sitar", "Mandolin", "Zither", "Ukulele",
                                 "Plucked string instrument"],
    "Brass": ["Brass instrument", "French horn", "Trumpet", "Trombone"],
    "Woodwinds": ["Wind instrument, woodwind instrument", "Flute", "Saxophone", "Clarinet"],
    "Accordion and harmonica": ["Harmonica", "Accordion", "Bagpipes", "Didgeridoo", "Shofar"],
}


@st.cache_resource(show_spinner=False)
def load_yamnet():
    import csv
    import tensorflow_hub as hub
    model = hub.load("https://tfhub.dev/google/yamnet/1")
    with open(model.class_map_path().numpy().decode("utf-8")) as f:
        names = [row["display_name"] for row in csv.DictReader(f)]
    return model, names


@st.cache_data(show_spinner=False)
def yamnet_scores(wave16k):
    model, _ = load_yamnet()
    scores, _, _ = model(wave16k)
    return scores.numpy()


def exp_instruments():
    with ctrl:
        scope = st.radio("Analyse", ["Whole song", "Selected segment"])
        thr = st.slider("Confidence threshold", 0.02, 0.60, 0.10, 0.01,
                        help="A moment counts as 'present' when the model's confidence is above this. "
                             "Mixed songs usually score low, so 0.05 to 0.20 works best.")
        minp = st.slider("Report if present in at least (% of audio)", 1, 50, 10)
    with out:
        try:
            with st.spinner("Loading the instrument model (first run downloads it)..."):
                _, names = load_yamnet()
        except Exception as e:
            st.error("The instrument model could not be loaded. Install the dependencies and make sure "
                     "you are online for the first run.")
            st.code("pip install tensorflow tensorflow-hub")
            st.caption(str(e)[:250])
            return

        src, off = (audio, 0.0) if scope == "Whole song" else (x, t_start)
        from math import gcd
        g = gcd(16000, SR)
        w16 = signal.resample_poly(src, 16000 // g, SR // g).astype(np.float32)
        w16 = w16 / max(1e-9, float(np.max(np.abs(w16))))
        if len(w16) < 16000:
            st.warning("Use at least one second of audio for instrument detection.")
            return
        with st.spinner("Listening to the audio..."):
            scores = yamnet_scores(w16)

        lower = {n.lower(): i for i, n in enumerate(names)}
        rows, series = [], {}
        for fam, classes in FAMILIES.items():
            idx = [lower[c.lower()] for c in classes if c.lower() in lower]
            if not idx:
                continue
            fs = scores[:, idx]
            s = fs.max(1)
            series[fam] = s
            rows.append({"Instrument": fam, "Best match": names[idx[int(np.argmax(fs.mean(0)))]],
                         "Present (% of audio)": round(float(np.mean(s >= thr) * 100), 1),
                         "Average confidence": round(float(s.mean()), 2),
                         "Peak confidence": round(float(s.max()), 2)})
        rows.sort(key=lambda r: (-r["Present (% of audio)"], -r["Average confidence"]))
        found = [r for r in rows if r["Present (% of audio)"] >= minp]
        ranked = found or sorted(rows, key=lambda r: -r["Average confidence"])

        if found:
            st.markdown("".join(f'<span class="badge">{html.escape(r["Instrument"])}</span>' for r in found),
                        unsafe_allow_html=True)
        else:
            st.info("Nothing passed the thresholds. The most likely instruments by average confidence are: "
                    + ", ".join(r["Instrument"] for r in ranked[:3])
                    + ". Try lowering the confidence threshold.")

        fig, (ax,) = stacked(1, 0.38 * len(rows) + 1.4)
        style(ax, "How much of the audio each instrument is present", "Present (% of audio)", "")
        ax.barh([r["Instrument"] for r in rows][::-1], [r["Present (% of audio)"] for r in rows][::-1],
                color=[TEAL if r["Present (% of audio)"] >= minp else EDGE for r in rows][::-1])
        ax.axvline(minp, color=AMBER, ls="--", lw=.8)
        ax.set_xlim(0, 100)
        ax.grid(False, axis="y")
        show(fig)

        top = [r["Instrument"] for r in ranked[:8]]
        if top:
            hop = 0.48
            tt0, tt1 = off + hop, off + hop * (len(scores) + 1)
            fig2, (ax2,) = stacked(1, 0.42 * len(top) + 1.4)
            style(ax2, "When each instrument appears", "Time (s)", "")
            ax2.grid(False)
            im = ax2.imshow(np.array([series[t] for t in top]), aspect="auto", cmap=CMAP, vmin=0,
                            vmax=max(0.3, float(max(series[t].max() for t in top))), extent=[tt0, tt1, len(top), 0], interpolation="nearest")
            ax2.set_yticks(np.arange(len(top)) + .5)
            ax2.set_yticklabels(top)
            cb = fig2.colorbar(im, ax=ax2, pad=.02)
            cb.set_label("Confidence", color=MUTED)
            cb.ax.tick_params(colors=MUTED, length=0)
            cb.outline.set_edgecolor(EDGE)
            show(fig2)

        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption("Detection uses YAMNet, a neural network trained on AudioSet. It is a good guide for common "
                   "instruments, but dense mixes, heavy effects and electronic sounds can fool it, so treat "
                   "the result as an estimate.")


EXPERIMENTS = {
    "Time domain": {
        "Waveform and statistics": (exp_waveform, "Inspect amplitude, energy, envelope and zero crossings of the segment."),
        "Time scaling (expand / compress)": (exp_scaling, "y(t) = x(at). Compressing in time raises every frequency by a, so pitch rises."),
        "Time shifting (delay / advance)": (exp_shift, "y(t) = x(t - t0). A shift changes the phase but not the magnitude spectrum."),
        "Time reversal": (exp_reverse, "y(t) = x(-t). The magnitude spectrum is unchanged and the phase is negated."),
        "Amplitude scaling and DC offset": (exp_amplitude, "y(t) = A x(t) + c. Too much gain clips the peaks and adds harmonic distortion."),
        "Echo (convolution)": (exp_echo, "An echo is convolution with a train of delayed, decaying impulses."),
        "Autocorrelation and pitch": (exp_autocorr, "The first strong autocorrelation peak after lag 0 marks the signal's period."),
    },
    "Frequency domain": {
        "Fourier transform (magnitude)": (exp_fft, "The FFT splits the segment into sinusoids. Window choice trades leakage against resolution."),
        "Phase spectrum": (exp_phase, "The phase gives the timing of each sinusoid. Try shifting a signal and compare."),
        "STFT": (exp_stft, "Windowed FFTs show how frequency content changes over time. Inspect single frames below the plot."),
        "Spectrogram": (exp_spectrogram, "The power version of the STFT, with scaling, colormap and log-frequency views."),
        "Filter design": (exp_filter, "Butterworth filters remove chosen bands. Compare the spectrum before and after, then listen."),
        "Spectral features": (exp_features, "Numbers that summarise the spectrum: centroid, bandwidth, roll-off and flatness."),
    },
    "Music analysis": {
        "Instrument detection": (exp_instruments, "A pretrained neural network listens to the song and reports which instruments are playing and when."),
    },
}


section("Choose an experiment", "Pick a domain, then an experiment. Results update as you change the parameters.", AMBER)
domain = st.radio("Domain", list(EXPERIMENTS), horizontal=True, label_visibility="collapsed")
name = st.selectbox("Experiment", list(EXPERIMENTS[domain]), key=domain)
func, theory = EXPERIMENTS[domain][name]
st.markdown(f'<div class="bench"><b>{name}</b><span>{theory}</span></div>', unsafe_allow_html=True)

ctrl, out = st.columns([1, 2.4], gap="large")
with ctrl:
    st.markdown("**Parameters**")
func()

st.markdown(FOOTER, unsafe_allow_html=True)