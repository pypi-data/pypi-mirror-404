"""Command-line interface for niimetric."""

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Tuple

from .utils import load_nifti, validate_shapes, normalize_to_range
from .cropping import auto_crop_volumes, get_crop_info
from .metrics import compute_ssim, compute_psnr, compute_mae, compute_lpips


def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="niimetric",
        description="Evaluate image quality metrics for NIfTI images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  niimetric -a reference.nii.gz -b image1.nii.gz --ssim -o output.csv
  niimetric -a reference.nii.gz -b image1.nii.gz --all -o results.csv
        """
    )
    
    # Required arguments
    parser.add_argument(
        "-a", "--reference",
        required=True,
        help="Path to reference NIfTI image (used for cropping boundaries)"
    )
    parser.add_argument(
        "-b", "--image",
        required=True,
        help="Path to comparison NIfTI image"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path to output CSV file"
    )
    
    # Metric selection
    metric_group = parser.add_argument_group("Metrics")
    metric_group.add_argument(
        "--ssim",
        action="store_true",
        help="Calculate Structural Similarity Index (SSIM)"
    )
    metric_group.add_argument(
        "--psnr",
        action="store_true",
        help="Calculate Peak Signal-to-Noise Ratio (PSNR)"
    )
    metric_group.add_argument(
        "--mae",
        action="store_true",
        help="Calculate Mean Absolute Error (MAE)"
    )
    metric_group.add_argument(
        "--lpips",
        action="store_true",
        help="Calculate Learned Perceptual Image Patch Similarity (LPIPS)"
    )
    metric_group.add_argument(
        "--all",
        action="store_true",
        help="Calculate all metrics"
    )
    
    return parser.parse_args(args)


def compute_metrics(
    ref_cropped: any,
    img_cropped: any,
    ssim: bool = False,
    psnr: bool = False,
    mae: bool = False,
    lpips: bool = False,
    all_metrics: bool = False
) -> List[Tuple[str, float]]:
    """
    Compute requested metrics on cropped volumes.
    
    Returns:
        List of (metric_name, value) tuples
    """
    results = []
    
    if psnr or all_metrics:
        print("  Computing PSNR...", flush=True)
        value = compute_psnr(ref_cropped, img_cropped)
        results.append(("PSNR", value))
        print(f"    PSNR: {value:.4f} dB")
    
    if ssim or all_metrics:
        print("  Computing SSIM...", flush=True)
        value = compute_ssim(ref_cropped, img_cropped)
        results.append(("SSIM", value))
        print(f"    SSIM: {value:.4f}")
    
    if mae or all_metrics:
        print("  Computing MAE...", flush=True)
        value = compute_mae(ref_cropped, img_cropped)
        results.append(("MAE", value))
        print(f"    MAE: {value:.4f}")
    
    if lpips or all_metrics:
        print("  Computing LPIPS (this may take a while)...", flush=True)
        value = compute_lpips(ref_cropped, img_cropped)
        results.append(("LPIPS", value))
        print(f"    LPIPS: {value:.4f}")
    
    return results


def write_csv(
    output_path: str,
    reference: str,
    image: str,
    results: List[Tuple[str, float]]
) -> None:
    """Write results to CSV file."""
    path = Path(output_path)
    file_exists = path.exists()
    
    with open(path, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if new file
        if not file_exists:
            writer.writerow(["reference", "image", "metric", "value"])
        
        # Write results
        ref_name = Path(reference).name
        img_name = Path(image).name
        for metric_name, value in results:
            writer.writerow([ref_name, img_name, metric_name, f"{value:.6f}"])


def main(args: List[str] = None) -> int:
    """Main entry point for the CLI."""
    parsed = parse_args(args)
    
    # Check that at least one metric is selected
    if not any([parsed.ssim, parsed.psnr, parsed.mae, parsed.lpips, parsed.all]):
        print("Error: Please specify at least one metric (--ssim, --psnr, --mae, --lpips, or --all)")
        return 1
    
    try:
        # Load images
        print(f"Loading reference: {parsed.reference}")
        ref_data = load_nifti(parsed.reference)
        print(f"  Shape: {ref_data.shape}")
        
        print(f"Loading image: {parsed.image}")
        img_data = load_nifti(parsed.image)
        print(f"  Shape: {img_data.shape}")
        
        # Validate shapes
        validate_shapes(ref_data, img_data)
        
        # Auto-crop based on reference
        print("Auto-cropping volumes based on reference...")
        ref_cropped, img_cropped, bbox = auto_crop_volumes(ref_data, img_data)
        crop_info = get_crop_info(bbox, ref_data.shape)
        print(f"  Original shape: {crop_info['original_shape']}")
        print(f"  Cropped shape: {crop_info['cropped_shape']}")
        print(f"  X range: {crop_info['x_range']}")
        print(f"  Y range: {crop_info['y_range']}")
        print(f"  Z range: {crop_info['z_range']}")
        
        # Normalize both images to 0-1 range
        print("Normalizing images to 0-1 range...")
        ref_normalized = normalize_to_range(ref_cropped, 0, 1)
        img_normalized = normalize_to_range(img_cropped, 0, 1)
        print(f"  Reference range: [{ref_cropped.min():.2f}, {ref_cropped.max():.2f}] -> [0, 1]")
        print(f"  Image range: [{img_cropped.min():.2f}, {img_cropped.max():.2f}] -> [0, 1]")
        
        # Compute metrics
        print("Computing metrics...")
        results = compute_metrics(
            ref_normalized, img_normalized,
            ssim=parsed.ssim,
            psnr=parsed.psnr,
            mae=parsed.mae,
            lpips=parsed.lpips,
            all_metrics=parsed.all
        )
        
        # Write to CSV
        write_csv(parsed.output, parsed.reference, parsed.image, results)
        print(f"\nResults written to: {parsed.output}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
