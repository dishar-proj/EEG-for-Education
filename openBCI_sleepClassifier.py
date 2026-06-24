# # EEG Research Analysis Tool for OpenBCI CSV

# import tkinter as tk
# from tkinter import filedialog, ttk
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# from scipy.signal import butter, filtfilt, welch, iirnotch, detrend

# FS = 200
# WINDOW_SEC = 30  # Standard clinical sleep epoch
# WINDOW = FS * WINDOW_SEC
# STEP = int(WINDOW)  

# # -------------------------------------------------
# # LOAD CSV
# # -------------------------------------------------
# def load_openbci_csv(path):
#     data = pd.read_csv(path, sep="\t", comment="%", header=None)
#     data = data.apply(pd.to_numeric, errors='coerce')
#     data = data.dropna()

#     signals = data.iloc[:, 1:5].values
#     return signals

# # -------------------------------------------------
# # FILTERS
# # -------------------------------------------------
# def bandpass_filter(signal, low=0.75, high=40, fs=FS, order=4):
#     nyq = 0.5 * fs
#     b, a = butter(order, [low/nyq, high/nyq], btype="band")
#     return filtfilt(b, a, signal, axis=0)

# def notch_filter(signal, freq=60, fs=FS):
#     b, a = iirnotch(freq, 30, fs)
#     return filtfilt(b, a, signal, axis=0)

# # -------------------------------------------------
# # BAND POWER
# # -------------------------------------------------
# def bandpower(psd, freqs, fmin, fmax):
#     idx = np.logical_and(freqs >= fmin, freqs <= fmax)
#     return np.trapezoid(psd[idx], freqs[idx])

# # -------------------------------------------------
# # ARTIFACT
# # -------------------------------------------------
# def detect_artifact(segment):
#     if np.max(np.ptp(segment, axis=0)) > 200:
#         return "Movement artifact"
#     if np.max(np.var(segment, axis=0)) > 1000:
#         return "Muscle artifact"
#     return "Clean"

# # -------------------------------------------------
# # FEATURE EXTRACTION 
# # -------------------------------------------------
# def analyze_eeg(signals):
#     filtered = bandpass_filter(signals, low=0.75, high=40)
#     filtered = notch_filter(filtered)

#     delta_series, theta_series, alpha_series, beta_series = [], [], [], []
#     spindle_flags, artifact_flags = [], []

#     for i in range(0, len(filtered) - WINDOW, STEP):
#         segment = filtered[i:i+WINDOW, :]
#         segment = detrend(segment, axis=0)

#         freqs, psd = welch(segment, FS, axis=0, nperseg=FS*4)
        
#         psd_front = np.mean(psd[:, 0:2], axis=1) if psd.shape[1] >= 2 else np.mean(psd, axis=1)
#         psd_occ = np.mean(psd[:, 2:4], axis=1) if psd.shape[1] >= 4 else np.mean(psd, axis=1)

#         total_front = bandpower(psd_front, freqs, 0.75, 30) + 1e-8
#         total_occ = bandpower(psd_occ, freqs, 0.75, 30) + 1e-8

#         delta = bandpower(psd_front, freqs, 0.75, 4) / total_front
#         theta = bandpower(psd_front, freqs, 4, 8) / total_front
#         alpha = bandpower(psd_occ, freqs, 8, 12) / total_occ
#         beta = bandpower(psd_front, freqs, 12, 30) / total_front

#         spindle = bandpower(psd_front, freqs, 11, 16) / total_front
#         spindle_flags.append(spindle > 0.08)
        
#         artifact_flags.append(detect_artifact(segment))

#         delta_series.append(delta)
#         theta_series.append(theta)
#         alpha_series.append(alpha)
#         beta_series.append(beta)

#     return delta_series, theta_series, alpha_series, beta_series, spindle_flags, artifact_flags

# # -------------------------------------------------
# # SLEEP ONSET 
# # -------------------------------------------------
# def detect_sleep_onset(theta, alpha):
#     ratio = np.array(theta) / (np.array(alpha) + 1e-6)
#     for i, r in enumerate(ratio):
#         if r > 1.2: 
#             return i * (STEP / FS)
#     return None

# # -------------------------------------------------
# # CLASSIFIER 
# # -------------------------------------------------
# def classify_sleep(delta, theta, alpha, beta, spindles, artifacts):
#     stages = []
#     prev_stage = "Awake"
    
#     # We now loop over the artifacts as well
#     for i, (d, t, a, b, s, art) in enumerate(zip(delta, theta, alpha, beta, spindles, artifacts)):
#         minutes_elapsed = (i * STEP / FS) / 60.0
        
#         # 1. ARTIFACT REJECTION OVERRIDE
#         # If the user is moving, it is impossible for them to be in N3 sleep.
#         if art != "Clean":
#             current_stage = "Awake"
            
#         # 2. BASE LOGIC
#         elif a > 0.15 and a > t:
#             current_stage = "Awake"
#         elif d > 0.65 and d > (t * 2.0):
#             if minutes_elapsed > 15.0:
#                 current_stage = "N3"
#             else:
#                 current_stage = "N2" if s else "N1"
#         # Relaxed N2 Delta threshold (0.45 instead of 0.50) to catch N2 even if spindles are missed by hardware
#         elif s or (d > 0.45 and t > 0.12):
#             current_stage = "N2"
#         elif t > 0.15 and t > a:
#             current_stage = "N1"
#         else:
#             current_stage = "Awake"
            
#         # 3. TRANSITION LOGIC
#         if current_stage == "N3" and prev_stage == "Awake":
#             current_stage = "N1" 
            
#         if current_stage == "N2" and prev_stage == "Awake" and not s:
#             current_stage = "N1" 
            
#         stages.append(current_stage)
#         prev_stage = current_stage
        
#     return stages

# # -------------------------------------------------
# # SMOOTHING
# # -------------------------------------------------
# def smooth_stages(stages, window=11):
#     smoothed = []
#     for i in range(len(stages)):
#         seg = stages[max(0,i-window//2):min(len(stages),i+window//2+1)]
#         smoothed.append(max(set(seg), key=seg.count))
#     return smoothed

# # -------------------------------------------------
# # ALPHA BLOCKING
# # -------------------------------------------------
# def alpha_blocking(alpha):
#     alpha = np.array(alpha)
#     low = np.percentile(alpha, 25)
#     high = np.percentile(alpha, 75)
#     detected = high > low * 1.5
#     return low, high, detected

# # -------------------------------------------------
# # SUMMARY
# # -------------------------------------------------
# def generate_summary(alpha, theta, delta, stages, sleep_onset):
#     text = []
#     if sleep_onset:
#         text.append(f"Possible drowsiness detected at {sleep_onset/60:.1f} min.")
    
#     text.append("Subject likely remained awake for the majority of the recording.")
    
#     if any(s == "N1" for s in stages):
#         text.append("Brief periods of drowsiness (N1) detected.")
    
#     if sum(1 for s in stages if s == "N2") > 2:
#         text.append("Possible light sleep episodes detected (low confidence).")
    
#     if np.mean(delta) < 0.25:
#         text.append("Little deep sleep detected.")
        
#     text.append("Overall: wakefulness with intermittent drowsiness, not sustained sleep.")
#     return " ".join(text)

# # -------------------------------------------------
# # PLOTS
# # -------------------------------------------------
# def plot_bandpower(delta, theta, alpha, beta, spindles):
#     plt.figure()
#     plt.plot(alpha, label="Alpha")
#     plt.plot(theta, label="Theta")
#     plt.plot(delta, label="Delta")
#     plt.plot(beta, label="Beta")
    
#     sp = [i for i,v in enumerate(spindles) if v]
#     plt.scatter(sp, [alpha[i] if i < len(alpha) else 0 for i in sp], marker="x", color='red')
    
#     plt.legend()
#     plt.title("Band Power")
#     plt.show()

# def plot_sleep_stages(stages):
#     mapping = {"Awake":0,"N1":1,"N2":2,"N3":3}
#     numeric = [mapping[s] for s in stages]
    
#     plt.figure()
#     plt.step(range(len(numeric)), numeric, where="mid")
#     plt.yticks([0,1,2,3],["Awake","N1","N2","N3"])
#     plt.title("Sleep Stages")
#     plt.show()

# # -------------------------------------------------
# # GUI
# # -------------------------------------------------
# class EEGApp:
#     def __init__(self, root):
#         self.root = root
#         root.title("EEG Research Analyzer")
        
#         frame = ttk.Frame(root, padding=20)
#         frame.pack()
        
#         ttk.Label(frame, text="OpenBCI EEG Tool", font=("Arial",16)).pack(pady=10)
#         ttk.Button(frame, text="Load CSV", command=self.load_file).pack(pady=5)
        
#         self.output = tk.Text(frame, width=70, height=20)
#         self.output.pack()

#     def log(self, msg):
#         self.output.insert(tk.END, msg + "\n")
#         self.output.see(tk.END)

#     def load_file(self):
#         path = filedialog.askopenfilename()
#         if not path:
#             return

#         signals = load_openbci_csv(path)
#         self.log("EEG file loaded (4 Channels)")

#         minutes = len(signals) / FS / 60
#         self.log(f"Recording length: {minutes:.2f} min")

#         delta, theta, alpha, beta, spindles, artifacts = analyze_eeg(signals)
#         sleep_onset = detect_sleep_onset(theta, alpha)
        
#         # We now pass the 'artifacts' array into the classifier to kill false N3 readings
#         stages = classify_sleep(delta, theta, alpha, beta, spindles, artifacts)
#         stages = smooth_stages(stages, window=11)

#         self.log("\nSleep Timeline")
#         if stages:
#             current_stage = stages[0]
#             start_idx = 0

#             for i in range(1, len(stages)):
#                 if stages[i] != current_stage:
#                     start_time = start_idx * (STEP / FS) / 60
#                     end_time = i * (STEP / FS) / 60
#                     self.log(f"{start_time:.2f}-{end_time:.2f} min : {current_stage}")
                    
#                     current_stage = stages[i]
#                     start_idx = i

#             final_start_time = start_idx * (STEP / FS) / 60
#             final_end_time = ((len(stages) - 1) * (STEP / FS) + WINDOW_SEC) / 60
#             self.log(f"{final_start_time:.2f}-{final_end_time:.2f} min : {current_stage}")

#         self.log(f"\nSpindles: {sum(spindles)}")
#         self.log(f"Artifacts: {sum(1 for a in artifacts if a!='Clean')}")

#         low, high, detected = alpha_blocking(alpha)
#         self.log(f"\nAlpha low: {low:.3f}")
#         self.log(f"Alpha high: {high:.3f}")
#         self.log("Alpha blocking detected" if detected else "Alpha blocking unclear")

#         summary = generate_summary(alpha, theta, delta, stages, sleep_onset)
#         self.log("\nSummary:")
#         self.log(summary)

#         plot_bandpower(delta, theta, alpha, beta, spindles)
#         plot_sleep_stages(stages)

# # -------------------------------------------------
# # MAIN
# # -------------------------------------------------
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = EEGApp(root)
#     root.mainloop()

# EEG Research Analysis Tool for OpenBCI CSV (Corrected Hybrid Logic & Original GUI)

# import tkinter as tk
# from tkinter import filedialog, ttk
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# from scipy.signal import butter, filtfilt, welch, iirnotch, detrend

# FS = 200
# WINDOW_SEC = 30  # Standard clinical sleep epoch
# WINDOW = FS * WINDOW_SEC
# STEP = int(WINDOW)  

# # -------------------------------------------------
# # LOAD CSV
# # -------------------------------------------------
# def load_openbci_csv(path):
#     data = pd.read_csv(path, sep="\t", comment="%", header=None)
#     data = data.apply(pd.to_numeric, errors='coerce')
#     data = data.dropna()
#     signals = data.iloc[:, 1:5].values
#     return signals

# # -------------------------------------------------
# # FILTERS
# # -------------------------------------------------
# def bandpass_filter(signal, low=0.75, high=40, fs=FS, order=4):
#     nyq = 0.5 * fs
#     b, a = butter(order, [low/nyq, high/nyq], btype="band")
#     return filtfilt(b, a, signal, axis=0)

# def notch_filter(signal, freq=60, fs=FS):
#     b, a = iirnotch(freq, 30, fs)
#     return filtfilt(b, a, signal, axis=0)

# def moving_rms(signal, window_size):
#     return np.sqrt(np.convolve(signal**2, np.ones(window_size)/window_size, mode='same'))

# # -------------------------------------------------
# # FEATURE EXTRACTION (Hybrid Logic)
# # -------------------------------------------------
# def analyze_eeg(signals):
#     filtered = bandpass_filter(signals, low=0.5, high=45)
#     filtered = notch_filter(filtered)

#     delta_series, theta_series, alpha_series, beta_series = [], [], [], []
#     spindle_flags, artifact_flags = [], []

#     for i in range(0, len(filtered) - WINDOW, STEP):
#         segment = filtered[i:i+WINDOW, :]
#         segment = detrend(segment, axis=0)

#         # 1. ARTIFACTS (Gross movement/Baseline wander)
#         max_ptp = np.max(np.ptp(segment, axis=0))
#         if max_ptp > 400:
#             artifact_flags.append("Movement artifact")
#         else:
#             artifact_flags.append("Clean")

#         # 2. TIME-DOMAIN SPINDLES (RMS Burst Detection)
#         front_ch = segment[:, 0] 
#         spindle_band = bandpass_filter(front_ch, 11.0, 16.0)
#         rms_envelope = moving_rms(spindle_band, window_size=int(FS*0.2))
#         rms_mean = np.mean(rms_envelope)
        
#         bursts = rms_envelope > (rms_mean * 1.3)
#         spindle_detected = False
#         burst_len = 0
#         for b in bursts:
#             if b:
#                 burst_len += 1
#             else:
#                 if 0.4 * FS <= burst_len <= 2.0 * FS:
#                     spindle_detected = True
#                     break
#                 burst_len = 0
#         spindle_flags.append(spindle_detected)

#         # 3. FREQUENCY DOMAIN (Relative Power)
#         freqs, psd = welch(segment, FS, axis=0, nperseg=FS*4)
#         psd_front = np.mean(psd[:, 0:2], axis=1) if segment.shape[1] >= 2 else np.mean(psd, axis=1)
#         psd_occ = np.mean(psd[:, 2:4], axis=1) if segment.shape[1] >= 4 else np.mean(psd, axis=1)

#         idx = np.logical_and(freqs >= 0.5, freqs <= 40)
#         total_front = np.trapezoid(psd_front[idx], freqs[idx]) + 1e-8
#         total_occ = np.trapezoid(psd_occ[idx], freqs[idx]) + 1e-8

#         def relative_power(psd_arr, fmin, fmax, total):
#             f_idx = np.logical_and(freqs >= fmin, freqs <= fmax)
#             return np.trapezoid(psd_arr[f_idx], freqs[f_idx]) / total

#         delta = relative_power(psd_front, 0.5, 4, total_front)
#         theta = relative_power(psd_front, 4, 8, total_front)
#         alpha = relative_power(psd_occ, 8, 12, total_occ)
#         beta = relative_power(psd_front, 12, 30, total_front)

#         delta_series.append(delta)
#         theta_series.append(theta)
#         alpha_series.append(alpha)
#         beta_series.append(beta)

#     return delta_series, theta_series, alpha_series, beta_series, spindle_flags, artifact_flags

# # -------------------------------------------------
# # SLEEP ONSET 
# # -------------------------------------------------
# def detect_sleep_onset(theta, alpha):
#     ratio = np.array(theta) / (np.array(alpha) + 1e-6)
#     for i, r in enumerate(ratio):
#         if r > 1.2: 
#             return i * (STEP / FS)
#     return None

# # -------------------------------------------------
# # CLASSIFIER (Dynamic Transition Logic)
# # -------------------------------------------------
# def classify_sleep(delta, theta, alpha, beta, spindles, artifacts):
#     stages = []
#     prev_stage = "Awake"
    
#     for i, (d, t, a, b, s, art) in enumerate(zip(delta, theta, alpha, beta, spindles, artifacts)):
#         # 1. Awake: Major artifacts or clear Alpha dominance
#         if art != "Clean":
#             current_stage = "Awake"
#         elif a > 0.25 and a > t:
#             current_stage = "Awake"
            
#         # 2. Light Sleep (N2): Spindles are the definitive marker of N2!
#         elif s:
#             current_stage = "N2"
            
#         # 3. Deep Sleep (N3): High Delta, but ONLY if we are already asleep
#         elif d > 0.55 and prev_stage in ["N2", "N3"]:
#             current_stage = "N3"
            
#         # 4. Drowsiness (N1): Theta replaces Alpha (Prioritized to catch the transition)
#         elif t > a and prev_stage in ["Awake", "N1"]:
#             current_stage = "N1"
            
#         # 5. Light Sleep (N2 Backup): High Theta + moderate Delta
#         # (Requires already being asleep so we don't jump from Awake straight to N2)
#         elif t > 0.20 and d > 0.35 and prev_stage != "Awake":
#             current_stage = "N2"
            
#         # 6. Fallback: Persist in current sleep state
#         else:
#             current_stage = prev_stage if prev_stage != "Awake" else "N1"
            
#         stages.append(current_stage)
#         prev_stage = current_stage
        
#     return stages

# # -------------------------------------------------
# # SMOOTHING (Rule-Based to Protect N1)
# # -------------------------------------------------
# def smooth_stages(stages, window=7):
#     smoothed = []
#     for i in range(len(stages)):
#         # Grab the local window
#         seg = stages[max(0, i - window//2) : min(len(stages), i + window//2 + 1)]
        
#         # Calculate the standard smoothed mode
#         mode_stage = max(set(seg), key=seg.count)
        
#         # EXCEPTION RULE: If the raw classifier detected N1, and the smoothing 
#         # is trying to overwrite it with Awake or N2, reject the smoothing and keep N1.
#         if stages[i] == "N1" and mode_stage in ["Awake", "N2"]:
#             smoothed.append("N1")
#         else:
#             smoothed.append(mode_stage)
            
#     return smoothed

# # -------------------------------------------------
# # ALPHA BLOCKING
# # -------------------------------------------------
# def alpha_blocking(alpha):
#     alpha = np.array(alpha)
#     low = np.percentile(alpha, 25)
#     high = np.percentile(alpha, 75)
#     detected = high > low * 1.5
#     return low, high, detected

# # -------------------------------------------------
# # SUMMARY (Fixed Dynamic Output)
# # -------------------------------------------------
# def generate_summary(alpha, theta, delta, stages, sleep_onset):
#     text = []
#     if sleep_onset:
#         text.append(f"Sleep onset detected at {sleep_onset/60:.1f} min.")
    
#     awake_percent = stages.count("Awake") / len(stages)
#     if awake_percent > 0.60:
#         text.append("Subject likely remained awake for the majority of the recording.")
#     elif awake_percent > 0.30:
#         text.append("Subject had highly fragmented sleep with frequent awakenings.")
#     else:
#         text.append("Subject successfully achieved sustained sleep.")
    
#     if any(s == "N1" for s in stages):
#         text.append("Brief periods of drowsiness (N1) detected.")
    
#     if stages.count("N2") > 5:
#         text.append("Clear light sleep (N2) episodes detected.")
    
#     if "N3" in stages:
#         text.append("Deep slow-wave sleep (N3) was achieved.")
#     else:
#         text.append("Little to no deep sleep detected.")
        
#     return " ".join(text)

# # -------------------------------------------------
# # PLOTS (Axes Labels Added)
# # -------------------------------------------------
# def plot_bandpower(delta, theta, alpha, beta, spindles):
#     plt.figure()
#     plt.plot(alpha, label="Alpha")
#     plt.plot(theta, label="Theta")
#     plt.plot(delta, label="Delta")
#     plt.plot(beta, label="Beta")
    
#     sp = [i for i,v in enumerate(spindles) if v]
#     plt.scatter(sp, [alpha[i] if i < len(alpha) else 0 for i in sp], marker="x", color='red')
    
#     plt.legend()
#     plt.title("Band Power")
#     plt.xlabel("Time (30-second Epochs)")
#     plt.ylabel("Relative Power (Ratio)")
#     plt.show()

# def plot_sleep_stages(stages):
#     mapping = {"Awake":0,"N1":1,"N2":2,"N3":3}
#     numeric = [mapping[s] for s in stages]
    
#     plt.figure()
#     plt.step(range(len(numeric)), numeric, where="mid")
#     plt.yticks([0,1,2,3],["Awake","N1","N2","N3"])
#     plt.title("Sleep Stages")
#     plt.xlabel("Time (30-second Epochs)")
#     plt.ylabel("Sleep Stage")
#     plt.show()

# # -------------------------------------------------
# # GUI (Original Formatting)
# # -------------------------------------------------
# class EEGApp:
#     def __init__(self, root):
#         self.root = root
#         root.title("EEG Research Analyzer")
        
#         frame = ttk.Frame(root, padding=20)
#         frame.pack()
        
#         ttk.Label(frame, text="OpenBCI EEG Tool", font=("Arial",16)).pack(pady=10)
#         ttk.Button(frame, text="Load CSV", command=self.load_file).pack(pady=5)
        
#         self.output = tk.Text(frame, width=70, height=20)
#         self.output.pack()

#     def log(self, msg):
#         self.output.insert(tk.END, msg + "\n")
#         self.output.see(tk.END)

#     def load_file(self):
#         path = filedialog.askopenfilename()
#         if not path:
#             return

#         signals = load_openbci_csv(path)
#         self.log("EEG file loaded (4 Channels)")

#         minutes = len(signals) / FS / 60
#         self.log(f"Recording length: {minutes:.2f} min")
#         self.root.update()

#         delta, theta, alpha, beta, spindles, artifacts = analyze_eeg(signals)
#         sleep_onset = detect_sleep_onset(theta, alpha)
        
#         stages = classify_sleep(delta, theta, alpha, beta, spindles, artifacts)
#         stages = smooth_stages(stages, window=7)

#         self.log("\nSleep Timeline")
#         if stages:
#             current_stage = stages[0]
#             start_idx = 0

#             for i in range(1, len(stages)):
#                 if stages[i] != current_stage:
#                     start_time = start_idx * (STEP / FS) / 60
#                     end_time = i * (STEP / FS) / 60
#                     self.log(f"{start_time:.2f}-{end_time:.2f} min : {current_stage}")
                    
#                     current_stage = stages[i]
#                     start_idx = i

#             final_start_time = start_idx * (STEP / FS) / 60
#             final_end_time = ((len(stages) - 1) * (STEP / FS) + WINDOW_SEC) / 60
#             self.log(f"{final_start_time:.2f}-{final_end_time:.2f} min : {current_stage}")

#         self.log(f"\nSpindles: {sum(spindles)}")
#         self.log(f"Artifacts: {sum(1 for a in artifacts if a!='Clean')}")

#         low, high, detected = alpha_blocking(alpha)
#         self.log(f"\nAlpha low: {low:.3f}")
#         self.log(f"Alpha high: {high:.3f}")
#         self.log("Alpha blocking detected" if detected else "Alpha blocking unclear")

#         summary = generate_summary(alpha, theta, delta, stages, sleep_onset)
#         self.log("\nSummary:")
#         self.log(summary)

#         plot_bandpower(delta, theta, alpha, beta, spindles)
#         plot_sleep_stages(stages)

# # -------------------------------------------------
# # MAIN
# # -------------------------------------------------
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = EEGApp(root)
#     root.mainloop()

import tkinter as tk
from tkinter import filedialog, ttk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, welch, iirnotch, detrend

FS = 200
WINDOW_SEC = 30  # Standard clinical sleep epoch
WINDOW = FS * WINDOW_SEC
STEP = int(WINDOW)  

# -------------------------------------------------
# LOAD CSV
# -------------------------------------------------
def load_openbci_csv(path):
    data = pd.read_csv(path, sep="\t", comment="%", header=None)
    data = data.apply(pd.to_numeric, errors='coerce')
    data = data.dropna()
    signals = data.iloc[:, 1:5].values
    return signals

# -------------------------------------------------
# FILTERS
# -------------------------------------------------
def bandpass_filter(signal, low=0.75, high=40, fs=FS, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, [low/nyq, high/nyq], btype="band")
    return filtfilt(b, a, signal, axis=0)

def notch_filter(signal, freq=60, fs=FS):
    b, a = iirnotch(freq, 30, fs)
    return filtfilt(b, a, signal, axis=0)

def moving_rms(signal, window_size):
    return np.sqrt(np.convolve(signal**2, np.ones(window_size)/window_size, mode='same'))

# -------------------------------------------------
# FEATURE EXTRACTION (Hybrid Logic)
# -------------------------------------------------
def analyze_eeg(signals):
    filtered = bandpass_filter(signals, low=0.5, high=45)
    filtered = notch_filter(filtered)

    delta_series, theta_series, alpha_series, beta_series = [], [], [], []
    spindle_flags, artifact_flags = [], []

    for i in range(0, len(filtered) - WINDOW, STEP):
        segment = filtered[i:i+WINDOW, :]
        segment = detrend(segment, axis=0)

        # 1. ARTIFACTS (Gross movement/Baseline wander)
        max_ptp = np.max(np.ptp(segment, axis=0))
        if max_ptp > 400:
            artifact_flags.append("Movement artifact")
        else:
            artifact_flags.append("Clean")

        # 2. TIME-DOMAIN SPINDLES (RMS Burst Detection)
        front_ch = segment[:, 0] 
        spindle_band = bandpass_filter(front_ch, 11.0, 16.0)
        rms_envelope = moving_rms(spindle_band, window_size=int(FS*0.2))
        rms_mean = np.mean(rms_envelope)
        
        bursts = rms_envelope > (rms_mean * 1.3)
        spindle_detected = False
        burst_len = 0
        for b in bursts:
            if b:
                burst_len += 1
            else:
                if 0.4 * FS <= burst_len <= 2.0 * FS:
                    spindle_detected = True
                    break
                burst_len = 0
        spindle_flags.append(spindle_detected)

        # 3. FREQUENCY DOMAIN (Relative Power)
        freqs, psd = welch(segment, FS, axis=0, nperseg=FS*4)
        psd_front = np.mean(psd[:, 0:2], axis=1) if segment.shape[1] >= 2 else np.mean(psd, axis=1)
        psd_occ = np.mean(psd[:, 2:4], axis=1) if segment.shape[1] >= 4 else np.mean(psd, axis=1)

        idx = np.logical_and(freqs >= 0.5, freqs <= 40)
        total_front = np.trapezoid(psd_front[idx], freqs[idx]) + 1e-8
        total_occ = np.trapezoid(psd_occ[idx], freqs[idx]) + 1e-8

        def relative_power(psd_arr, fmin, fmax, total):
            f_idx = np.logical_and(freqs >= fmin, freqs <= fmax)
            return np.trapezoid(psd_arr[f_idx], freqs[f_idx]) / total

        delta = relative_power(psd_front, 0.5, 4, total_front)
        theta = relative_power(psd_front, 4, 8, total_front)
        alpha = relative_power(psd_occ, 8, 12, total_occ)
        beta = relative_power(psd_front, 12, 30, total_front)

        delta_series.append(delta)
        theta_series.append(theta)
        alpha_series.append(alpha)
        beta_series.append(beta)

    return delta_series, theta_series, alpha_series, beta_series, spindle_flags, artifact_flags

# -------------------------------------------------
# SLEEP ONSET 
# -------------------------------------------------
def detect_sleep_onset(theta, alpha):
    ratio = np.array(theta) / (np.array(alpha) + 1e-6)
    for i, r in enumerate(ratio):
        if r > 1.2: 
            return i * (STEP / FS)
    return None

# -------------------------------------------------
# CLASSIFIER (Dynamic Transition Logic)
# -------------------------------------------------
def classify_sleep(delta, theta, alpha, beta, spindles, artifacts):
    stages = []
    prev_stage = "Awake"
    
    for i, (d, t, a, b, s, art) in enumerate(zip(delta, theta, alpha, beta, spindles, artifacts)):
        # 1. Awake: Major artifacts or clear Alpha dominance
        if art != "Clean":
            current_stage = "Awake"
        elif a > 0.25 and a > t:
            current_stage = "Awake"
            
        # 2. Light Sleep (N2): Spindles are the definitive marker of N2!
        elif s:
            current_stage = "N2"
            
        # 3. Deep Sleep (N3): High Delta, but ONLY if we are already asleep
        elif d > 0.55 and prev_stage in ["N2", "N3"]:
            current_stage = "N3"
            
        # 4. Drowsiness (N1): Theta replaces Alpha (Prioritized to catch the transition)
        elif t > a and prev_stage in ["Awake", "N1"]:
            current_stage = "N1"
            
        # 5. Light Sleep (N2 Backup): High Theta + moderate Delta
        elif t > 0.20 and d > 0.35 and prev_stage != "Awake":
            current_stage = "N2"
            
        # 6. Fallback: Persist in current sleep state
        else:
            current_stage = prev_stage if prev_stage != "Awake" else "N1"
            
        stages.append(current_stage)
        prev_stage = current_stage
        
    return stages

# -------------------------------------------------
# SMOOTHING (Rule-Based to Protect N1)
# -------------------------------------------------
def smooth_stages(stages, window=7):
    smoothed = []
    for i in range(len(stages)):
        seg = stages[max(0, i - window//2) : min(len(stages), i + window//2 + 1)]
        mode_stage = max(set(seg), key=seg.count)
        
        if stages[i] == "N1" and mode_stage in ["Awake", "N2"]:
            smoothed.append("N1")
        else:
            smoothed.append(mode_stage)
            
    return smoothed

# -------------------------------------------------
# ALPHA BLOCKING
# -------------------------------------------------
def alpha_blocking(alpha):
    alpha = np.array(alpha)
    low = np.percentile(alpha, 25)
    high = np.percentile(alpha, 75)
    detected = high > low * 1.5
    return low, high, detected

# -------------------------------------------------
# SUMMARY (Fixed Dynamic Output)
# -------------------------------------------------
def generate_summary(alpha, theta, delta, stages, sleep_onset):
    text = []
    if sleep_onset:
        text.append(f"Sleep onset detected at {sleep_onset/60:.1f} min.")
    
    awake_percent = stages.count("Awake") / len(stages)
    if awake_percent > 0.60:
        text.append("Subject likely remained awake for the majority of the recording.")
    elif awake_percent > 0.30:
        text.append("Subject had highly fragmented sleep with frequent awakenings.")
    else:
        text.append("Subject successfully achieved sustained sleep.")
    
    if any(s == "N1" for s in stages):
        text.append("Brief periods of drowsiness (N1) detected.")
    
    if stages.count("N2") > 5:
        text.append("Clear light sleep (N2) episodes detected.")
    
    if "N3" in stages:
        text.append("Deep slow-wave sleep (N3) was achieved.")
    else:
        text.append("Little to no deep sleep detected.")
        
    return " ".join(text)

# -------------------------------------------------
# PLOTS (Auto-Find Clean Data)
# -------------------------------------------------
def plot_raw_vs_filtered(signals, fs=FS, duration_sec=5, channel_idx=0):
    raw_channel = signals[:, channel_idx]
    
    # Pre-filter to evaluate where the clean data is
    filtered_channel = bandpass_filter(raw_channel, low=0.5, high=45, fs=fs)
    filtered_channel = notch_filter(filtered_channel, freq=60, fs=fs)
    
    window_size = duration_sec * fs
    best_start_idx = 0
    lowest_noise = float('inf')
    
    # Auto-Search: Scan the first 5 minutes to find the quietest 5 seconds
    search_limit = min(len(filtered_channel) - window_size, fs * 60 * 5)
    for i in range(0, search_limit, window_size):
        segment = filtered_channel[i : i + window_size]
        ptp = np.ptp(segment) # Peak-to-peak amplitude
        
        # We want the quietest segment that isn't totally dead/disconnected (>10uV)
        if 10 < ptp < lowest_noise:
            lowest_noise = ptp
            best_start_idx = i
            
    start_idx = best_start_idx
    end_idx = start_idx + window_size
    
    raw_segment = raw_channel[start_idx:end_idx]
    filtered_segment = filtered_channel[start_idx:end_idx]
    
    time_axis = np.linspace(0, duration_sec, len(raw_segment))
    
    plt.figure(figsize=(10, 6))
    
    plt.subplot(2, 1, 1)
    plt.plot(time_axis, raw_segment, color='gray')
    plt.title("Raw EEG Signal (Environmental Noise & DC Drift)")
    plt.ylabel("Amplitude (µV)")
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.plot(time_axis, filtered_segment, color='blue')
    plt.title("Filtered EEG Signal (0.5-45 Hz Bandpass + 60 Hz Notch)")
    plt.xlabel("Time (Seconds)")
    plt.ylabel("Amplitude (µV)")
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def plot_bandpower(delta, theta, alpha, beta, spindles):
    plt.figure()
    plt.plot(alpha, label="Alpha")
    plt.plot(theta, label="Theta")
    plt.plot(delta, label="Delta")
    plt.plot(beta, label="Beta")
    
    sp = [i for i,v in enumerate(spindles) if v]
    plt.scatter(sp, [alpha[i] if i < len(alpha) else 0 for i in sp], marker="x", color='red')
    
    plt.legend()
    plt.title("Band Power")
    plt.xlabel("Time (30-second Epochs)")
    plt.ylabel("Relative Power (Ratio)")
    plt.show()

def plot_sleep_stages(stages):
    mapping = {"Awake":0,"N1":1,"N2":2,"N3":3}
    numeric = [mapping[s] for s in stages]
    
    plt.figure()
    plt.step(range(len(numeric)), numeric, where="mid")
    plt.yticks([0,1,2,3],["Awake","N1","N2","N3"])
    plt.title("Sleep Stages")
    plt.xlabel("Time (30-second Epochs)")
    plt.ylabel("Sleep Stage")
    plt.show()

# -------------------------------------------------
# GUI 
# -------------------------------------------------
class EEGApp:
    def __init__(self, root):
        self.root = root
        root.title("EEG Research Analyzer")
        
        frame = ttk.Frame(root, padding=20)
        frame.pack()
        
        ttk.Label(frame, text="OpenBCI EEG Tool", font=("Arial",16)).pack(pady=10)
        ttk.Button(frame, text="Load CSV", command=self.load_file).pack(pady=5)
        
        self.output = tk.Text(frame, width=70, height=20)
        self.output.pack()

    def log(self, msg):
        self.output.insert(tk.END, msg + "\n")
        self.output.see(tk.END)

    def load_file(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        signals = load_openbci_csv(path)
        self.log("EEG file loaded (4 Channels)")

        minutes = len(signals) / FS / 60
        self.log(f"Recording length: {minutes:.2f} min")
        self.root.update()

        delta, theta, alpha, beta, spindles, artifacts = analyze_eeg(signals)
        sleep_onset = detect_sleep_onset(theta, alpha)
        
        stages = classify_sleep(delta, theta, alpha, beta, spindles, artifacts)
        stages = smooth_stages(stages, window=7)

        self.log("\nSleep Timeline")
        if stages:
            current_stage = stages[0]
            start_idx = 0

            for i in range(1, len(stages)):
                if stages[i] != current_stage:
                    start_time = start_idx * (STEP / FS) / 60
                    end_time = i * (STEP / FS) / 60
                    self.log(f"{start_time:.2f}-{end_time:.2f} min : {current_stage}")
                    
                    current_stage = stages[i]
                    start_idx = i

            final_start_time = start_idx * (STEP / FS) / 60
            final_end_time = ((len(stages) - 1) * (STEP / FS) + WINDOW_SEC) / 60
            self.log(f"{final_start_time:.2f}-{final_end_time:.2f} min : {current_stage}")

        self.log(f"\nSpindles: {sum(spindles)}")
        self.log(f"Artifacts: {sum(1 for a in artifacts if a!='Clean')}")

        low, high, detected = alpha_blocking(alpha)
        self.log(f"\nAlpha low: {low:.3f}")
        self.log(f"Alpha high: {high:.3f}")
        self.log("Alpha blocking detected" if detected else "Alpha blocking unclear")

        summary = generate_summary(alpha, theta, delta, stages, sleep_onset)
        self.log("\nSummary:")
        self.log(summary)

        # Draw plots
        plot_raw_vs_filtered(signals)
        plot_bandpower(delta, theta, alpha, beta, spindles)
        plot_sleep_stages(stages)

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = EEGApp(root)
    root.mainloop()