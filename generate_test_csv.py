import numpy as np
import pandas as pd

fs = 200
minutes = 10
duration = minutes * 60

t = np.arange(0, duration, 1/fs)

def eeg_stage(freqs, amps, noise_level, mask):
    sig = np.zeros(mask.sum())
    for f,a in zip(freqs,amps):
        sig += a*np.sin(2*np.pi*f*t[mask])
    sig += np.random.normal(0,noise_level,mask.sum())
    return sig

ch0 = np.zeros(len(t))
ch1 = np.zeros(len(t))
ch2 = np.zeros(len(t))
ch3 = np.zeros(len(t))

# Awake (0–2 min) – alpha dominant
awake = (t < 120)

ch0[awake] = eeg_stage([10,20],[45,10],8,awake)
ch1[awake] = eeg_stage([10,18],[40,8],8,awake)
ch2[awake] = eeg_stage([10,22],[42,9],8,awake)
ch3[awake] = eeg_stage([10,19],[38,10],8,awake)

# N1 (2–4 min) – theta increases
n1 = (t >= 120) & (t < 240)

ch0[n1] = eeg_stage([6,10],[35,15],8,n1)
ch1[n1] = eeg_stage([6,10],[30,15],8,n1)
ch2[n1] = eeg_stage([6,9],[32,14],8,n1)
ch3[n1] = eeg_stage([6,10],[34,13],8,n1)

# N2 (4–7 min)
n2 = (t >= 240) & (t < 420)

ch0[n2] = eeg_stage([6,2],[30,25],7,n2)
ch1[n2] = eeg_stage([6,2],[28,24],7,n2)
ch2[n2] = eeg_stage([6,2],[29,26],7,n2)
ch3[n2] = eeg_stage([6,2],[27,23],7,n2)

# N3 (7–10 min) – delta dominant
n3 = (t >= 420)

ch0[n3] = eeg_stage([2,4],[50,12],6,n3)
ch1[n3] = eeg_stage([2,4],[48,10],6,n3)
ch2[n3] = eeg_stage([2,4],[52,11],6,n3)
ch3[n3] = eeg_stage([2,4],[47,9],6,n3)

df = pd.DataFrame({
    "Sample Index": np.arange(len(t)),
    "EXG Channel 0": ch0,
    "EXG Channel 1": ch1,
    "EXG Channel 2": ch2,
    "EXG Channel 3": ch3
})

df.to_csv("openbci_simulated_sleep.csv", index=False)

print("Created openbci_simulated_sleep.csv")