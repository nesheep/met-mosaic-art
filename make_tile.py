import os
import sys
from pathlib import Path

import pyvips


def make_tile(src: str, dest: str, tile_size: int) -> None:
    img = pyvips.Image.new_from_file(src)
    w, h = img.width, img.height
    if w < tile_size and h < tile_size:
        print("passed")
        return
    htw = w < h
    img = img.resize(tile_size / (w if htw else h), kernel=pyvips.enums.Kernel.NEAREST)
    if htw:
        img = img.crop(0, (img.height - tile_size) / 2, tile_size, tile_size)
    else:
        img = img.crop((img.width - tile_size) / 2, 0, tile_size, tile_size)
    img.write_to_file(dest)
    print("saved")


def main() -> None:
    src_dir = Path(sys.argv[1])
    dest_dir = Path(sys.argv[2])
    tile_size = int(sys.argv[3])

    dest_dir.mkdir(parents=True, exist_ok=True)

    raw_files = os.listdir(src_dir)
    total = len(raw_files)

    for i, f in enumerate(raw_files):
        src = str(src_dir / f)
        dest = str(dest_dir / f)
        print(f"{i + 1}/{total} {src} -> {dest}")
        try:
            make_tile(src, dest, tile_size)
        except:
            print("error")


if __name__ == "__main__":
    main()
