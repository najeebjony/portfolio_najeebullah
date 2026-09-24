import os
import sys
from pathlib import Path
from PIL import Image, ImageOps

def optimize_image(image_path: Path, output_dir: Path, max_dimension: int = 1600, quality: int = 85):
    """
    Optimizes a single image:
    - Maintains EXIF orientation using exif_transpose
    - Resizes to max_dimension on the longest side (if larger)
    - Saves as JPEG/WebP copy without overwriting original
    """
    try:
        with Image.open(image_path) as img:
            # Correct orientation from EXIF tags
            img = ImageOps.exif_transpose(img)
            
            # Convert RGBA to RGB for JPEG compatibility if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            width, height = img.size
            if max(width, height) > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"Resized {image_path.name} from {width}x{height} to {new_width}x{new_height}")
            else:
                print(f"{image_path.name} is within {max_dimension}px ({width}x{height})")
                
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{image_path.stem}.opt.jpg"
            
            # Never overwrite original file
            if output_file.resolve() == image_path.resolve():
                output_file = output_dir / f"{image_path.stem}_opt.jpg"
                
            img.save(output_file, "JPEG", quality=quality, optimize=True)
            print(f"Saved optimized copy: {output_file}")
            return output_file
    except Exception as e:
        print(f"Error optimizing {image_path}: {e}")
        return None

def optimize_all_images(images_dir: Path = None, output_dir: Path = None):
    base_dir = Path(__file__).resolve().parent.parent
    if images_dir is None:
        images_dir = base_dir / "frontend" / "assets" / "images"
    if output_dir is None:
        output_dir = images_dir / "optimized"

    if not images_dir.exists():
        print(f"Images directory not found: {images_dir}")
        return

    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    found_any = False
    for path in images_dir.iterdir():
        if path.is_file() and path.suffix.lower() in extensions and not path.name.endswith(".opt.jpg"):
            found_any = True
            optimize_image(path, output_dir)

    if not found_any:
        print(f"No original images found in {images_dir}")

if __name__ == "__main__":
    optimize_all_images()
