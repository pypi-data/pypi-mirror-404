import matplotlib.pyplot as plt
import numpy as np
import colorsys
import json
import os

def display_movie_barcode(avg_colors, show_axes=True, title=None):
    """
    Displays average colors as a 'Movie Barcode'.
    
    Parameters:
    - avg_colors: list of (R, G, B) tuples.
    - show_axes: bool, if False, removes all text, titles, and axes.
    - title: str, optional title. Defaults to standard title if None and show_axes is True.
    """
    barcode_data = np.array(avg_colors, dtype=np.uint8).reshape(1, -1, 3)
    
    plt.figure(figsize=(15, 3))
    plt.imshow(barcode_data, aspect='auto', interpolation='nearest')
    
    if not show_axes:
        plt.axis('off')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    else:
        # Determine which title to use
        display_title = title if title is not None else "Movie Color Barcode (One sliver per second)"
        plt.title(display_title)
        
        plt.xlabel("Time (Seconds)")
        plt.yticks([])  # Hide Y-axis
        plt.tight_layout()
        
    plt.show()


def plot_rgb_3d(avg_colors):
    """
    Plots the average colors as points in a 3D space (R, G, B axes).
    Each point is colored by the actual color it represents.
    """
    # 1. Prepare data
    # Convert to numpy array for easy slicing
    colors_array = np.array(avg_colors) 
    
    # Matplotlib needs colors in range 0-1, so we divide by 255
    norm_colors = colors_array / 255.0
    
    # 2. Setup 3D Plot
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 3. Plot Scatter
    # x=Red, y=Green, z=Blue
    ax.scatter(
        xs=colors_array[:, 0], 
        ys=colors_array[:, 1], 
        zs=colors_array[:, 2], 
        c=norm_colors,  # This maps the dot color to the data itself
        s=50,           # Size of dots
        alpha=0.8       # Transparency helps if dots overlap
    )
    
    # 4. Labeling
    ax.set_xlabel('Red Channel')
    ax.set_ylabel('Green Channel')
    ax.set_zlabel('Blue Channel')
    ax.set_title('3D Color Distribution')
    
    # Set limits to standard 0-255 RGB space
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 255)
    ax.set_zlim(0, 255)
    
    plt.show()


def plot_hsv_polar(avg_colors):
    """
    Plots colors on a polar projection.
    Angle = Hue, Radius = Saturation.
    """
    hues = []
    sats = []
    vals = []
    colors = []

    for rgb in avg_colors:
        # Normalize to 0-1
        r, g, b = [x/255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        # Matplotlib polar plot expects angles in radians
        hues.append(h * 2 * np.pi) 
        sats.append(s)
        vals.append(v)
        colors.append((r, g, b))

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='polar')

    # Scatter plot
    c = ax.scatter(hues, sats, c=colors, s=50, alpha=0.75)
    
    ax.set_title("HSV Color Wheel Analysis", y=1.08)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['Gray', 'Muted', 'Vibrant', 'Neon'])
    
    plt.show()


def display_and_save_barcode(avg_colors, show_name, season, episode, fps=1.0, save_format="png", output_file_path=None):
    """
    Displays a clean 'Movie Barcode' (no axes or text) and optionally saves it with embedded metadata.

    Parameters:
    - avg_colors: list of (R, G, B) tuples.
    - show_name: str, name of the show (required for metadata).
    - season: str or int, season number (required for metadata).
    - episode: str or int, episode number (required for metadata).
    - fps: float, frames per second used for extraction (default 1.0).
    - save_format: str, file format 'png' or 'svg' (default 'png').
    - output_file_path: str, optional path to save the image. If provided, saves the file.
    """
    barcode_data = np.array(avg_colors, dtype=np.uint8).reshape(1, -1, 3)

    plt.figure(figsize=(15, 3))
    plt.imshow(barcode_data, aspect='auto', interpolation='nearest')
    
    plt.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    if output_file_path:
        sanitized_colors = [[int(c) for c in rgb] for rgb in avg_colors]

        metadata_dict = {
            "show_name": show_name,
            "season": season,
            "episode": episode,
            "frame_count": len(avg_colors),
            "fps": fps,
            "average_colors": sanitized_colors
        }

        metadata_json = json.dumps(metadata_dict)

        image_metadata = {
            "Title": f"{show_name} S{season}E{episode}",
            "Description": metadata_json
        }

        if save_format.lower() == 'png':
            image_metadata["Software"] = "moviesigdb"

        if not output_file_path.lower().endswith(f".{save_format}"):
            output_file_path += f".{save_format}"

        plt.savefig(output_file_path, format=save_format, metadata=image_metadata, bbox_inches='tight', pad_inches=0)
        print(f"Saved barcode to {output_file_path}")

    plt.show()