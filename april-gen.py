import cv2
import numpy as np
from pupil_apriltags import Detector
import os


def generate_apriltags(n: int, output_dir: str = "apriltags", dpi: int = 96):
    """
    Generate N AprilTags of tag36h11 family as 100x100mm PNG images.

    Args:
        n: Number of AprilTags to generate (IDs 0 to n-1)
        output_dir: Directory to save the PNG files
        dpi: Dots per inch for size calculation (default 96)
    """
    os.makedirs(output_dir, exist_ok=True)

    # Convert 100mm to pixels: (mm / 25.4) * dpi
    size_px = int((100 / 25.4) * dpi)  # ~378 pixels at 96 DPI

    # Tag36h11 has a 6x6 bit grid + 1-bit border = 8x8 total grid
    # We'll use OpenCV's AprilTag drawing or manual rendering
    # Using the robotpy-apriltag or dt-apriltags library

    try:
        import apriltag

        use_apriltag_lib = True
    except ImportError:
        use_apriltag_lib = False

    if use_apriltag_lib:
        _generate_with_apriltag_lib(n, output_dir, size_px)
    else:
        _generate_with_opencv(n, output_dir, size_px)


def _generate_with_opencv(n: int, output_dir: str, size_px: int):
    """Generate using OpenCV's AprilTag dictionary."""
    # OpenCV uses DICT_APRILTAG_36h11
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)

    for i in range(n):
        # Generate marker image (raw tag without white border)
        # markerSize controls internal pixel grid; we'll resize after
        marker_px = 200  # generate at higher res, then resize
        tag_img = cv2.aruco.generateImageMarker(aruco_dict, i, marker_px)

        # Add white border (~1 tag cell wide = 1/8 of marker)
        border_size = marker_px // 8
        tag_with_border = cv2.copyMakeBorder(
            tag_img,
            border_size,
            border_size,
            border_size,
            border_size,
            cv2.BORDER_CONSTANT,
            value=255,
        )

        # Resize to target size (100x100mm at chosen DPI)
        final_img = cv2.resize(
            tag_with_border, (size_px, size_px), interpolation=cv2.INTER_NEAREST
        )

        filename = os.path.join(output_dir, f"AprilTag_{i}.png")
        cv2.imwrite(filename, final_img)
        print(f"Saved: {filename}")


def _generate_with_apriltag_lib(n: int, output_dir: str, size_px: int):
    """Generate using the apriltag library."""
    import apriltag

    fam = apriltag.tag36h11()
    for i in range(n):
        tag = fam.generate_image(i, size=size_px, border=1)
        tag_img = np.array(tag)

        filename = os.path.join(output_dir, f"AprilTag_{i}.png")
        cv2.imwrite(filename, tag_img)
        print(f"Saved: {filename}")


if __name__ == "__main__":
    N = int(input("Enter number of AprilTags to generate: "))
    generate_apriltags(n=N, output_dir="apriltags", dpi=96)
    print(f"\nDone! {N} AprilTags saved in the 'apriltags/' folder.")
