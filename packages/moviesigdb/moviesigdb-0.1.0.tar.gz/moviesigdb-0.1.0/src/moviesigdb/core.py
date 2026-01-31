import os
import cv2
import numpy as np
from tqdm import tqdm

def get_video_capture(video_path):
    """
    Validates a video path and returns a cv2.VideoCapture object.

    Parameters:
    - video_path: str, the absolute path to the video file.

    Returns:
    - cap: cv2.VideoCapture object if successful.
    
    Raises:
    - FileNotFoundError: If the path does not exist.
    - IOError: If the video file cannot be opened by OpenCV.
    """
    if not os.path.isabs(video_path):
        raise ValueError(f"Path must be absolute. Received: {video_path}")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"No file found at: {video_path}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise IOError(f"OpenCV could not open the video file at: {video_path}")

    return cap


def extract_frames_fast(cap, processing_fps=1.0):
    """
    Extracts frames from a video at a specified rate with a visual progress bar.

    Parameters:
    - cap: cv2.VideoCapture object.
    - processing_fps: float, frames to extract per second of video (default 1.0).
      Example: 1.0 = 1 frame/sec, 0.5 = 1 frame every 2 secs, 2.0 = 2 frames/sec.

    Returns:
    - frames: list of NumPy arrays (RGB) extracted from the video.
    """
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Safety check for video_fps to avoid division by zero
    if video_fps <= 0:
        video_fps = 24.0

    step_size = video_fps / processing_fps
    total_steps = int(total_frames / step_size)
    
    frames = []
    
    for i in tqdm(range(total_steps), desc="Processing Video", unit="frame"):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i * step_size))
        
        ret, frame = cap.read()
        if not ret:
            break
            
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
    return frames


def get_average_colors(frames_list):
    """
    Calculates the average RGB color for each frame in the list.

    Parameters:
    - frames_list: list of NumPy arrays (RGB).

    Returns:
    - avg_colors: list of tuples, each containing (R, G, B) average values.
    """
    avg_colors = []
    
    for frame in frames_list:
        # Calculate mean across axis 0 (height) and 1 (width)
        # result is an array of [R_avg, G_avg, B_avg]
        avg_rgb = np.mean(frame, axis=(0, 1))
        
        # Convert to tuple and append
        avg_colors.append(tuple(avg_rgb.astype(int)))
        
    return avg_colors