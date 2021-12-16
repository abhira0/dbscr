from pyrhd.utility.cprint import printInfo
from dbdl.magoosh import MAG_D, MAG_H, MAG_IDM
from dbdl.magoosh.constants import CW, TMP_I
from dbdl.scrolller import SLR_D, SLR_H, SLR_DUPY
import argparse

DOWNLOAD_PATH = "F:\scr"


def MAG_GRE(a):
    MAG_H(DOWNLOAD_PATH, "info") if not a.noharvest else None
    MAG_D(DOWNLOAD_PATH, "info") if a.download else None
    # MAG_IDM(DOWNLOAD_PATH, "info")


def SLR(a):
    sub_name = (a.q or input("Sub name: ")).strip()
    SLR_H(sub_name, DOWNLOAD_PATH, "info") if not a.noharvest else None
    SLR_D(sub_name, DOWNLOAD_PATH, "info") if a.download else None
    # SLR_DUPY(DOWNLOAD_PATH)


def argument_owner():
    a = argparse.ArgumentParser()
    a.add_argument(
        "-s",
        help="Website URL to scrape",
        default=None,
        nargs="?",
    )
    a.add_argument(
        "-q",
        help="Query to pass into the website (if any)",
        default=None,
        nargs="?",
    )
    a.add_argument(
        "-d", "--download", help="Whether to download or not", action="store_true"
    )
    a.add_argument(
        "-nh", "--noharvest", help="Do not need to harvest?", action="store_true"
    )
    a.add_argument(
        "-dp",
        help="Download Path",
        default=None,
        nargs="?",
    )
    return a


ao = argument_owner()
a = ao.parse_args()


# total_files = len(list(Utils.os.getAllFiles(DOWNLOAD_PATH)))

if a.dp:
    DOWNLOAD_PATH = a.dp


if not a.s:
    ao.print_help()
elif "scrolller.com" in a.s:
    SLR(a)
elif "gre.magoosh.com" in a.s:
    MAG_GRE(a)
else:
    printInfo(*TMP_I, "Currently, given website is not supported by the program.", CW)
