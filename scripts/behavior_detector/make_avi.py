"""Script for taking front and side folders of all trials stores as jpg images and making them into avi videos."""

import argparse
from pathlib import Path
from tqdm import tqdm
import re
import os
import cv2


def get_index(path):
    # extracts number from image_2496.jpeg → 2496
    return int(re.search(r"(\d+)", os.path.basename(path)).group())


def make_avis(input_path, output_path, prefix, fps=167):
    trials = list(input_path.glob("v*"))
    for t in tqdm(trials):
        images = list(t.glob("*.jpg"))
        images = sorted(images, key=get_index)

        first = cv2.imread(images[0])
        h, w = first.shape[:2]

        fourcc = cv2.VideoWriter_fourcc(*"XVID")  # best AVI compatibility

        output = output_path.joinpath(f"{prefix}_side_{t.stem}.avi")
        writer = cv2.VideoWriter(output, fourcc, fps, (w, h))

        for f in images:
            frame = cv2.imread(f)
            writer.write(frame)

        writer.release()


if __name__ == "__main__":
    # get command line args
    parser = argparse.ArgumentParser(description="Parse command line arguments")

    parser.add_argument(
        "input_folder", help="Path to folder containing side/ and front/ subfolders."
    )
    parser.add_argument(
        "prefix", help="Prefix for each output video (i.e. rb50_20250125)"
    )

    # 3. Parse the arguments
    args = parser.parse_args()

    INPUT_FOLDER = Path(args.input_folder)
    if not INPUT_FOLDER.exists():
        raise FileNotFoundError(f"Input folder {INPUT_FOLDER} does not exist")
    PREFIX = str(args.prefix)

    OUTPUT_FOLDER = INPUT_FOLDER.joinpath("videos")
    if not OUTPUT_FOLDER.exists():
        print("Making output dir")
        os.mkdir(OUTPUT_FOLDER)

    SIDE_FOLDER = INPUT_FOLDER.joinpath("side")
    if not SIDE_FOLDER.exists():
        print("No side folder found")
    else:
        make_avis(SIDE_FOLDER, OUTPUT_FOLDER, PREFIX)

    FRONT_FOLDER = INPUT_FOLDER.joinpath("front")
    if not FRONT_FOLDER.exists():
        print("No front folder found")
    else:
        make_avis(FRONT_FOLDER, OUTPUT_FOLDER, PREFIX)
