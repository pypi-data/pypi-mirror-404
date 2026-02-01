# NiiMetric

A Python CLI tool for evaluating image quality metrics between NIfTI (.nii/.nii.gz) images.

## Features

- **SSIM** - Structural Similarity Index
- **PSNR** - Peak Signal-to-Noise Ratio
- **MAE** - Mean Absolute Error
- **LPIPS** - Learned Perceptual Image Patch Similarity
- **Auto-cropping** - Automatically crops to brain region based on reference image
- **CSV output** - Save results to CSV file

## Installation

```bash
pip install niimetric
```

## Usage

```bash
# Single metric
niimetric -a reference.nii.gz -b image1.nii.gz --ssim -o output.csv
niimetric -a reference.nii.gz -b image1.nii.gz --psnr -o output.csv
niimetric -a reference.nii.gz -b image1.nii.gz --mae -o output.csv
niimetric -a reference.nii.gz -b image1.nii.gz --lpips -o output.csv

# All metrics
niimetric -a reference.nii.gz -b image1.nii.gz --all -o output.csv
```

## Arguments

| Argument | Description |
|----------|-------------|
| `-a, --reference` | Reference NIfTI image (used for cropping boundaries) |
| `-b, --image` | Comparison NIfTI image |
| `-o, --output` | Output CSV file path |
| `--ssim` | Calculate SSIM |
| `--psnr` | Calculate PSNR |
| `--mae` | Calculate MAE |
| `--lpips` | Calculate LPIPS |
| `--all` | Calculate all metrics |

## License

MIT
