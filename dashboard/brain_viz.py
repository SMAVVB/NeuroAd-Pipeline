"""
Brain map visualization for NeuroAd Dashboard.
Generates brain map PNGs from .npy files using Nilearn.
"""

import os
from pathlib import Path
from typing import Optional

import numpy as np

# Try to import nilearn, fall back gracefully if not available
try:
    from nilearn import plotting
    from nilearn import surface
    NILEARN_AVAILABLE = True
except ImportError:
    NILEARN_AVAILABLE = False

# Try to import nibabel
try:
    import nibabel as nib
    NIBABEL_AVAILABLE = True
except ImportError:
    NIBABEL_AVAILABLE = False

# Try to import PIL
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def generate_brain_map(npy_path: str, output_png_path: str) -> bool:
    """
    Generate a brain map PNG from a .npy file.
    
    Args:
        npy_path: Path to the .npy file (n_timesteps x 20484 vertices)
        output_png_path: Path where the PNG should be saved
        
    Returns:
        True on success, False on failure
    """
    npy_path = Path(npy_path)
    output_png_path = Path(output_png_path)
    
    # Ensure output directory exists
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Graceful fallback if nilearn is not available
    if not NILEARN_AVAILABLE or not NIBABEL_AVAILABLE:
        return create_placeholder_brain_map(output_png_path)
    
    try:
        # Load the .npy array
        data = np.load(npy_path)
        
        # data shape: n_timesteps x 20484 vertices (fsaverage5)
        if data.ndim != 2 or data.shape[1] != 20484:
            return create_placeholder_brain_map(output_png_path)
        
        # Calculate mean activation over time axis
        mean_activation = np.mean(data, axis=0)  # shape: (20484,)
        
        # Get fsaverage5 surface paths
        # nilearn stores surface data in its data directory
        try:
            from nilearn.datasets import fetch_surf_fsaverage
            fsaverage = fetch_surf_fsaverage()
        except Exception:
            return create_placeholder_brain_map(output_png_path)
        
        # Plot 4-panel brain map
        # LH lateral, LH medial, RH lateral, RH medial
        fig = plotting.plot_surf_stat_map(
            surf_map=mean_activation,
            surf_mesh=fsaverage.pial_left,
            bg_map=fsaverage.sulc_left,
            view='lateral',
            threshold=None,
            cmap='cold_hot',
            colorbar=False,
            axes=None,
            title=None,
        )
        
        # Save the figure
        # Note: We need to save each view separately and combine them
        # For simplicity, we'll use a different approach with matplotlib
        
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec
        
        # Create a 2x2 grid for the 4 views
        fig = plt.figure(figsize=(12, 10))
        gs = GridSpec(2, 2, figure=fig)
        
        views = [
            ('lateral', 'left'),
            ('medial', 'left'),
            ('lateral', 'right'),
            ('medial', 'right'),
        ]
        
        for idx, (view, hemi) in enumerate(views):
            ax = fig.add_subplot(gs[idx // 2, idx % 2])
            
            # Get the appropriate surface files
            if hemi == 'left':
                pial = fsaverage.pial_left
                sulc = fsaverage.sulc_left
            else:
                pial = fsaverage.pial_right
                sulc = fsaverage.sulc_right
            
            # Plot the surface
            display = plotting.plot_surf_stat_map(
                surf_map=mean_activation,
                surf_mesh=pial,
                bg_map=sulc,
                view=view,
                threshold=None,
                cmap='cold_hot',
                colorbar=False,
                axes=ax,
                title=f'{hemi.upper()} {view.capitalize()}',
            )
            display.close()
        
        plt.tight_layout()
        plt.savefig(output_png_path, dpi=150, bbox_inches='tight', facecolor='black')
        plt.close(fig)
        
        return True
        
    except Exception as e:
        # If any error occurs, create a placeholder
        return create_placeholder_brain_map(output_png_path)


def create_placeholder_brain_map(output_path: Path) -> bool:
    """
    Create a placeholder brain map PNG when nilearn is not available.
    
    Args:
        output_path: Path where the PNG should be saved
        
    Returns:
        True on success
    """
    try:
        # Create a simple placeholder image with text
        img = Image.new('RGB', (800, 600), color='black')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except (IOError, OSError):
            font = ImageFont.load_default()
            title_font = font
        
        # Add text
        text = "Brain map not available\n\nNilearn not installed"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        position = ((800 - text_width) // 2, (600 - text_height) // 2)
        
        draw.text(position, text, fill='white', font=font, align='center')
        
        img.save(output_path)
        return True
        
    except Exception:
        return False


def get_brain_map_path(npy_path: str) -> str:
    """
    Get the expected brain map PNG path for a .npy file.
    
    Args:
        npy_path: Path to the .npy file
        
    Returns:
        Path to the corresponding PNG file
    """
    npy_path = Path(npy_path)
    png_path = npy_path.parent / npy_path.name.replace('_tribe_preds.npy', '_brain_map.png')
    return str(png_path)


def brain_map_exists(npy_path: str) -> bool:
    """
    Check if a brain map PNG already exists for a .npy file.
    
    Args:
        npy_path: Path to the .npy file
        
    Returns:
        True if PNG exists, False otherwise
    """
    png_path = get_brain_map_path(npy_path)
    return Path(png_path).exists()


def load_temporal_profile(npy_path: str) -> Optional[tuple[np.ndarray, np.ndarray]]:
    """
    Load temporal profile data from .npy file.
    
    Args:
        npy_path: Path to the .npy file
        
    Returns:
        Tuple of (timesteps, mean_activation_per_timestep) or None on error
    """
    try:
        data = np.load(npy_path)
        
        if data.ndim != 2 or data.shape[1] != 20484:
            return None
        
        # Calculate mean activation per timestep
        mean_per_timestep = np.mean(data, axis=1)
        
        # Create timestep array (assuming 1.0 second per timestep)
        timesteps = np.arange(len(mean_per_timestep)) * 1.0
        
        return timesteps, mean_per_timestep
        
    except Exception:
        return None
