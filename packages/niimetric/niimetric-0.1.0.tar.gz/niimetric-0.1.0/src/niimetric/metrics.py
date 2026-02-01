"""Image quality metrics for NIfTI volumes."""

import numpy as np
from skimage.metrics import structural_similarity, peak_signal_noise_ratio
from typing import Optional


def compute_psnr(ref: np.ndarray, img: np.ndarray, data_range: Optional[float] = None) -> float:
    """
    Compute Peak Signal-to-Noise Ratio (PSNR).
    
    Args:
        ref: Reference image
        img: Comparison image
        data_range: The data range of the images. If None, computed from reference.
        
    Returns:
        PSNR value in dB
    """
    if data_range is None:
        data_range = ref.max() - ref.min()
    
    return float(peak_signal_noise_ratio(ref, img, data_range=data_range))


def compute_ssim(ref: np.ndarray, img: np.ndarray, data_range: Optional[float] = None) -> float:
    """
    Compute Structural Similarity Index (SSIM).
    
    For 3D volumes, computes SSIM with appropriate window size.
    
    Args:
        ref: Reference image
        img: Comparison image
        data_range: The data range of the images. If None, computed from reference.
        
    Returns:
        SSIM value between -1 and 1 (higher is better)
    """
    if data_range is None:
        data_range = ref.max() - ref.min()
    
    # Determine appropriate win_size based on smallest dimension
    min_dim = min(ref.shape)
    win_size = min(7, min_dim if min_dim % 2 == 1 else min_dim - 1)
    if win_size < 3:
        win_size = 3
    
    return float(structural_similarity(
        ref, img, 
        data_range=data_range,
        win_size=win_size,
        channel_axis=None  # No channel axis for 3D grayscale
    ))


def compute_mae(ref: np.ndarray, img: np.ndarray) -> float:
    """
    Compute Mean Absolute Error (MAE).
    
    Args:
        ref: Reference image
        img: Comparison image
        
    Returns:
        MAE value (lower is better)
    """
    return float(np.mean(np.abs(ref - img)))


def compute_lpips(ref: np.ndarray, img: np.ndarray) -> float:
    """
    Compute Learned Perceptual Image Patch Similarity (LPIPS).
    
    LPIPS is designed for 2D images, so for 3D volumes we compute
    the average LPIPS across all axial slices.
    
    Args:
        ref: Reference 3D volume
        img: Comparison 3D volume
        
    Returns:
        Average LPIPS value (lower is better)
    """
    import torch
    import lpips
    
    # Initialize LPIPS model (using AlexNet by default)
    loss_fn = lpips.LPIPS(net='alex', verbose=False)
    
    # Move to GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    loss_fn = loss_fn.to(device)
    
    # Normalize to [-1, 1] range as expected by LPIPS
    ref_min, ref_max = ref.min(), ref.max()
    if ref_max - ref_min > 0:
        ref_norm = 2 * (ref - ref_min) / (ref_max - ref_min) - 1
        img_norm = 2 * (img - ref_min) / (ref_max - ref_min) - 1
    else:
        ref_norm = np.zeros_like(ref)
        img_norm = np.zeros_like(img)
    
    # Compute LPIPS slice by slice along the last axis (axial slices)
    lpips_values = []
    
    with torch.no_grad():
        for z in range(ref.shape[2]):
            # Get 2D slices
            ref_slice = ref_norm[:, :, z]
            img_slice = img_norm[:, :, z]
            
            # Convert to tensor: (1, 3, H, W) - replicate grayscale to 3 channels
            ref_tensor = torch.from_numpy(ref_slice).float().unsqueeze(0).unsqueeze(0)
            ref_tensor = ref_tensor.repeat(1, 3, 1, 1).to(device)
            
            img_tensor = torch.from_numpy(img_slice).float().unsqueeze(0).unsqueeze(0)
            img_tensor = img_tensor.repeat(1, 3, 1, 1).to(device)
            
            # Compute LPIPS
            lpips_val = loss_fn(ref_tensor, img_tensor)
            lpips_values.append(lpips_val.item())
    
    return float(np.mean(lpips_values))
