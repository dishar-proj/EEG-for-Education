# EEG for Education

## Signal Reliability and Sleep Stage Detection Using AI-Assisted Analysis

**Chair's Choice Award Recipient — UGA ECE Expo 2026**

---

## Overview

Medical-grade electroencephalography (EEG) systems can be expensive and require specialized equipment and training, limiting their accessibility for student-led and self-directed research.

EEG for Education investigates whether the lower-cost OpenBCI Ganglion can provide sufficiently reliable EEG data for controlled physiological experiments and exploratory sleep analysis.

The project combines experimental EEG validation with a Python-based signal-processing and sleep-stage classification pipeline. Controlled trials were conducted with and without conductive electrode paste to evaluate signal reliability, alpha blocking, and motor-related activity. In addition, sleep recordings were analyzed using frequency-domain features and rule-based classification.

The project also explores the potential of generative AI as an assistive tool for interpreting EEG data in educational research environments.

---

## Research Objectives

This project addresses four primary questions:

1. How does conductive electrode paste affect the reliability of EEG recordings collected with the OpenBCI Ganglion?
2. Can a low-cost EEG system reproduce established physiological patterns such as alpha blocking?
3. Can the recorded data support basic classification of sleep stages?
4. How can generative AI assist with EEG interpretation while remaining secondary to quantitative signal analysis?

---

## Experimental Design

EEG data was collected using the OpenBCI Ganglion, a four-channel EEG acquisition system operating at a sampling rate of 200 Hz.

Controlled validation experiments included:

- Eyes-open versus eyes-closed trials to evaluate alpha blocking
- Resting versus finger-tapping trials to examine motor-related activity
- Recordings collected with conductive electrode paste
- Recordings collected without conductive electrode paste
- Sleep recordings used to evaluate stage classification

The controlled experiments were designed to determine whether the recorded signals demonstrated patterns consistent with established EEG behavior.

---

## Signal Processing Pipeline

The Python analysis pipeline processes OpenBCI recordings in 30-second epochs. The current implementation applies a 0.5–45 Hz band-pass filter followed by a 60 Hz notch filter before feature extraction. :contentReference[oaicite:2]{index=2}

The processing workflow is:

```text
OpenBCI EEG Recording
        |
        v
CSV Data Import
        |
        v
Band-Pass Filtering
        |
        v
60 Hz Notch Filtering
        |
        v
30-Second Epoch Segmentation
        |
        v
Artifact Detection
        |
        v
Power Spectral Density Analysis
        |
        v
EEG Band-Power Extraction
        |
        v
Spindle Detection
        |
        v
Sleep Stage Classification
        |
        v
Sleep Timeline and Visualization

```

## How to Run

1. Run the program:

```bash
python openBCI_sleepClassifier.py

```
2. Click Load CSV.
3. Select an OpenBCI EEG recording.
4. Review the generated sleep-stage timeline, EEG band-power analysis, artifact detection, spindle detection, and signal-processing plots.
