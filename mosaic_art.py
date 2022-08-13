import math
import os
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyvips
from PIL import Image


def ndarray2vips(arr: np.ndarray) -> pyvips.Image:
    """np.ndarray -> pyvips.Image

    Args:
        arr (np.ndarray): shape = (*, *, 3), dtype = uint8

    Returns:
        pyvips.Image: image
    """
    h, w, b = arr.shape
    linear = arr.reshape(w * h * b)
    return pyvips.Image.new_from_memory(linear.data, w, h, b, 'uchar')


def color_avg(im: np.ndarray) -> np.ndarray:
    """color avarage

    Args:
        im (np.ndarray): shape = (*, *, 3), dtype = uint8

    Returns:
        np.ndarray: shape = (3,), dtype = uint8
    """
    a = np.zeros((3), np.uint64)
    for y in range(im.shape[0]):
        for x in range(im.shape[1]):
            a = a + im[y, x]
    a = a / (im.shape[0] * im.shape[1])
    return np.round(a).astype(np.uint8)


def make_tiles_dict(tiles_dir: Path) -> dict[str, np.ndarray]:
    """make {tile: color_average} dict

    Args:
        tiles_dir (Path): tiles dir

    Returns:
        dict[str, np.ndarray]: value shape = (3,), dtype = uint8
    """
    d = {}
    files = os.listdir(tiles_dir)
    file_num = len(files)
    for i, t in enumerate(files):
        print(f"color avarage: {i + 1}/{file_num} {t}")
        t_im = np.array(Image.open(tiles_dir / t))
        if t_im.ndim != 3:
            continue
        if t_im.shape[2] != 3:
            continue
        d[t] = color_avg(t_im)
    return d


def change_color(tile: Path, avg: np.ndarray, color: np.ndarray) -> np.ndarray:
    """change tile color 'avg' to 'color'

    Args:
        tile (Path): tile
        avg (np.ndarray): shape = (3,), dtype = uint8
        color (np.ndarray): shape = (3,), dtype = uint8

    Returns:
        np.ndarray: shape = (*, *, 3), dtype = uint8
    """
    im = np.array(Image.open(tile))
    avg = avg.astype(np.int16)
    color = color.astype(np.int16)
    diff = color - avg
    c_im = im + diff
    return np.clip(c_im, 0, 255).astype(np.uint8)


def save_row(src_row: np.ndarray, dest: Path, tiles_dict: dict[str, np.ndarray], tiles_dir: Path, tile_size: int) -> None:
    """make and save mossaic art row

    Args:
        src_row (np.ndarray): shape = (*, 3), dtype = uint8
        dest (Path): dest path
        tiles_dict (dict[str, np.ndarray]): value shape = (3,), dtype = uint8
        tiles_dir (Path): tiles dir path
        tile_size (int): tile size
    """
    print(f"save row: {dest}")
    w, h = tile_size * src_row.shape[0], tile_size

    row_im = pyvips.Image.black(w, h, bands=3)  # type: ignore
    for x in range(src_row.shape[0]):
        t, avg = random.choice(list(tiles_dict.items()))
        t_im = ndarray2vips(change_color(tiles_dir / t, avg, src_row[x]))
        row_im = row_im.insert(t_im, tile_size * x, 0)

    row_im.write_to_file(str(dest))


def save_mosaic(src_im: np.ndarray, dest: Path, tmp_dir: Path, tile_size: int) -> None:
    """make and save mosaic art

    Args:
        src_im (np.ndarray): shape = (*, *, 3), dtype = uint8
        dest (Path): dest path
        tmp_dir (Path): tmp dir path
        tile_size (int): tile size
    """
    w, h = tile_size * src_im.shape[1], tile_size * src_im.shape[0]
    im = pyvips.Image.black(w, h, bands=3)  # type: ignore

    for y in range(src_im.shape[0]):
        row_im = pyvips.Image.new_from_file(str(tmp_dir / f"{y}.v"))
        im = im.insert(row_im, 0, tile_size * y)

    im.tiffsave(
        str(dest),
        tile=True,
        pyramid=True,
        compression="jpeg",
        Q=20,
        tile_width=256,
        tile_height=256,
        bigtiff=True,
    )


def main() -> None:
    src_file = Path(sys.argv[1])
    dest_file = Path(sys.argv[2])
    tiles_dir = Path(sys.argv[3])
    tile_size = int(sys.argv[4])
    max_worker = int(sys.argv[5])

    src_im = np.array(Image.open(src_file))
    t_dict = make_tiles_dict(tiles_dir)

    tmp_dir = Path("./tmp")

    for i in range(math.ceil(src_im.shape[0] / max_worker)):
        with ProcessPoolExecutor(max_worker) as executor:
            for j in range(max_worker):
                y = i * max_worker + j
                if y >= src_im.shape[0]:
                    break
                dest = tmp_dir / f"{y}.v"
                executor.submit(save_row, src_im[y], dest, t_dict, tiles_dir, tile_size)

    print(f"save mosaic: {dest_file}")
    with ProcessPoolExecutor(1) as executor:
        executor.submit(save_mosaic, src_im, dest_file, tmp_dir, tile_size)


if __name__ == "__main__":
    main()
