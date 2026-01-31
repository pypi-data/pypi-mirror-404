# moviesigdb: The Movie Color DNA Analyzer

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

**moviesigdb** is a powerful Python toolkit designed to extract, visualize, and archive the color palette of video files. By condensing thousands of frames into a single "Movie Barcode" or projecting them into 3D space, you can analyze the cinematography, mood, and lighting evolution of any film or TV episode.

> **What is a Movie Barcode?** > It is a time-compressed visualization where every vertical slice of the image represents the average color of a specific moment in the video.

---

## 📸 Visualization Capabilities

**moviesigdb** goes beyond simple stripes. It offers three distinct ways to view your data:

1.  **The Barcode:** A linear timeline of the video's color.
2.  **3D RGB Cube:** Plots every frame as a point in 3D space (Red, Green, Blue axes) to show color clusters and separation.
3.  **HSV Polar Wheel:** Maps the mood.
    * **Angle** = Hue (Color)
    * **Radius** = Saturation (Intensity)
    * *Great for seeing if a movie is "Teal and Orange" or "Neon Noir".*

---

## 🚀 Features

* **Smart Extraction:** Uses `tqdm` to show a real-time progress bar while processing large video files.
* **Adjustable Granularity:** Extract 1 frame per second, 10 frames per second, or 1 frame per minute using the `processing_fps` parameter.
* **Metadata Archiving:** Uniquely embeds JSON data (Show Name, Season, Episode, FPS) directly into the output PNG file headers.
* **Scientific Plotting:** Leverages `matplotlib` for high-resolution, publication-quality figures.

---

## 📦 Installation

### Option 1: From Source (Recommended)
Cloning the repo allows you to modify the source code easily.

```bash
git clone [https://github.com/shreyanbruh/moviesigdb.git](https://github.com/shreyanbruh/moviesigdb.git)
cd moviesigdb
pip install -e .
```



```python 
import moviesigdb as msdb

# 1. Load your video
video_path = "path/to/your_video.mp4"
cap = msdb.get_video_capture(video_path)

# 2. Extract frames (e.g., 1 frame per second)
frames = msdb.extract_frames_fast(cap, processing_fps=1.0)

# 3. Calculate average colors
avg_colors = msdb.get_average_colors(frames)

# 4. Display the results
msdb.display_movie_barcode(avg_colors, title="My Movie Analysis")
msdb.plot_hsv_polar(avg_colors)
```