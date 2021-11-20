from dbdl.magoosh import MAG_D, MAG_H, MAG_IDM
from dbdl.scrolller import SLR_D, SLR_H

DOWNLOAD_PATH = "F:\scr"


def MAG_GRE():
    MAG_H(DOWNLOAD_PATH, "info")
    MAG_D(DOWNLOAD_PATH, "info")
    # MAG_IDM(DOWNLOAD_PATH, "info")


def SLR():
    sub_name = "ImaginaryCaves"
    SLR_H(sub_name, DOWNLOAD_PATH, "info")
    SLR_D(sub_name, DOWNLOAD_PATH, "info")
