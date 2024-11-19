import os
import shutil


def move_file(filename, path, moveto):
    files = os.listdir(path)
    files.sort()
    for f in files:
        if f == filename:
            src = path+f
            dst = moveto+f
            shutil.move(src, dst)
