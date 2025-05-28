import cv2
import os
import argparse

# Define the desired width and height of the cropped rectangle
CROP_WIDTH = 600
CROP_HEIGHT = 500

# Define the offset for the crop center
X_OFFSET = -100
Y_OFFSET = +150

def center_crop(image, w, h):
    cx = w // 2 + X_OFFSET
    cy = h // 2 + Y_OFFSET

    x1 = max(cx - CROP_WIDTH // 2, 0)
    y1 = max(cy - CROP_HEIGHT // 2, 0)
    x2 = min(cx + CROP_WIDTH // 2, w)
    y2 = min(cy + CROP_HEIGHT // 2, h)

    return image[y1:y2, x1:x2]

def crop_folder_images(folder_path, output_dir="clipped"):
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(folder_path):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        input_path = os.path.join(folder_path, filename)
        image = cv2.imread(input_path)
        if image is None:
            print(f"Skipping unreadable file: {filename}")
            continue

        h, w = image.shape[:2]
        cropped = center_crop(image, w, h)

        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, cropped)
        print(f"Saved: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="Path to folder containing images")
    args = parser.parse_args()

    crop_folder_images(args.folder)