import random
from json import dumps
from threading import BoundedSemaphore, Thread
import threading
from time import time
from typing import List, Optional

from pyrhd.downloader.dler import BaseDownloader
from pyrhd.utility.cprint import aprint, deleteLines, printInfo

from .constants import *
from .utility import Utils as UTL


class Downloader(BaseDownloader):
    def __init__(
        self,
        sub_name: str,
        download_path: str,
        randomize: bool = False,
        refresh: bool = False,
        verbose: Optional[str] = "min",
    ):
        self.randomize = randomize
        start_time = time()
        if verbose == "info":
            aprint("\n>>>", CA, "Downloader\n", CB)
        tmp_s = ["Downloader", CC, "for", CN, f"{ROOT_URL}r/{sub_name}", CU]
        tmp_s += ["has been instantiated", CN]
        printInfo(*TMP_I, *tmp_s)

        self.download_path = f"{download_path}\\{BASE_PATH}\\{sub_name}\\media"
        ultimatum_path = f"{download_path}\\{BASE_PATH}\\{sub_name}\\{sub_name}.json"
        UTL.os.makedirs(self.download_path)
        super().__init__(ultimatum_path, SAVING_INTERVAL)

        if refresh:
            self.refreshDownloads()
        self.download()
        self.quitSaver()

        if verbose == "info":
            aprint("\n>>>", CA, "Downloader-End\n", CB)
        tmp_s = ["Time taken for", CN, "Downloader", CC, "class to complete is", CN]
        time_taken = round(time() - start_time, 6)
        printInfo(*TMP_I, *tmp_s, time_taken, CT, "seconds", CN)

    def download(self):
        self.sema4 = BoundedSemaphore(CONF["thread"]["download"])
        self.thr: List[Thread] = []
        self.al_thr: List[Thread] = []
        self.downloadAlbums()
        self.downloadPicsVids()
        # deleteLines(2)
        UTL.threading.joinThreads(self.al_thr)
        UTL.threading.joinThreads(self.thr)
        self.saveUltimatum()
        self.printVerbose(2)

    def downloadAlbums(self):
        gen_item = self.ultimatum["albums"].items()
        al_sema4 = BoundedSemaphore(CONF["thread"]["album"])
        if self.randomize:

            def tmp_fun():
                r = list(self.ultimatum["albums"])
                random.shuffle(r)
                for i in r:
                    yield i, self.ultimatum["albums"][i]

            gen_item = tmp_fun()
        for album_url, album_info in gen_item:
            media_set = set(album_info["mediaUrls"] if album_info["mediaUrls"] else [])
            downloaded_set = set(
                album_info["downloaded"] if album_info["downloaded"] else []
            )
            diff_list = media_set - downloaded_set
            if diff_list == set():
                continue
            al_sema4.acquire()
            args = [[album_url, album_info, diff_list, al_sema4], self.thr]
            UTL.threading.createThread(self.downloadAnAlbum, *args)

    def downloadAnAlbum(
        self,
        album_url: str,
        album_info: dict,
        diff_list: set,
        al_sema4: BoundedSemaphore,
    ):
        sub_folder = album_info["title"].replace(".", "")[:40].strip()
        __path = f"{self.download_path}\\{sub_folder}"
        UTL.os.makedir(__path)
        for media_url in diff_list:
            self.sema4.acquire()
            args = [[album_url, media_url, __path], self.al_thr]
            UTL.threading.createThread(self.downloadAlMed, *args)
        al_sema4.release()

    def downloadAlMed(self, album_url, media_url, __path):
        if self.downloadMedia(media_url, __path, None, None):
            self.ultimatum["albums"][album_url]["downloaded"].append(media_url)

    def downloadPicsVids(self):
        u_media = self.ultimatum["medias"]
        gen_item = u_media.items()
        if self.randomize:

            def tmp_fun():
                r = list(u_media)
                random.shuffle(r)
                for i in r:
                    yield i, u_media[i]

            gen_item = tmp_fun()
        for parent_url, media_info in gen_item:
            if u_media[parent_url]["downloaded"]:
                continue
            self.sema4.acquire()
            args = [[parent_url, media_info], self.thr]
            UTL.threading.createThread(self.downloadAPicVid, *args)

    def downloadAPicVid(self, parent_url, media_info):
        title = media_info["title"]
        _id = parent_url.split("-")[-1].strip()
        media_url = media_info["mediaUrl"]
        if self.downloadMedia(media_url, self.download_path, title, _id):
            self.ultimatum["medias"][parent_url]["downloaded"] = True

    def downloadMedia(
        self,
        media_url: str,
        media_path: str,
        title: str,
        _id: str = None,
    ) -> bool:
        status = False
        try:
            url_filename, ex10sion = media_url.split("/")[-1].split(".")
            ex10sion = ex10sion.split("?")[0] if "?" in ex10sion else ex10sion
            if title:
                title = title.replace(".", "")[:40]
                title = fr"{title}-{_id}.{ex10sion}"
            else:
                if _id == None:
                    _id = url_filename.split("-")[-1]
                url_filename = url_filename.replace(".", "")[:40]
                title = fr"{url_filename}-{_id}.{ex10sion}"
            if self.downloadAMedia(media_url, media_path, title, None, True, False):
                # deleteLines(2)
                # aprint("✅ Downloaded video from", CS, media_url, CU)
                self.printVerbose(1)
                status = True
        except:
            printInfo(*TMP_E, "Error in the function: Downloader.downloadMedia")
        self.sema4.release()
        return status

    def getCount(self, mode: str) -> int:
        c = 0
        if mode == "med":
            for i, j in self.ultimatum["medias"].items():
                c += j["downloaded"]
        elif mode == "alb":
            for album_url, album_info in self.ultimatum["albums"].items():
                media_set = set(
                    album_info["mediaUrls"] if album_info["mediaUrls"] else []
                )
                downloaded_set = set(
                    album_info["downloaded"] if album_info["downloaded"] else []
                )
                diff_list = media_set - downloaded_set
                if diff_list == set():
                    c += 1
        return c

    def printVerbose(self, stage: int):
        if stage == 1:
            tmed = len(self.ultimatum["medias"])
            talb = len(self.ultimatum["albums"])
            fmed = self.getCount("med")
            falb = self.getCount("alb")
            tmp_s = [*TMP_I, fmed, CT, "/", CN, tmed, CT, "medias and", CN]
            tmp_s += [falb, CT, "/", CN, talb, CT, "albums has been downloaded", CN]
            tmp_s += ["[threadCount:", CN, threading.activeCount(), CT, "]", CN]
            printInfo(*tmp_s, same_line=True)
        if stage == 2:
            tmed = len(self.ultimatum["medias"])
            talb = len(self.ultimatum["albums"])
            fmed = self.getCount("med")
            falb = self.getCount("alb")
            tmp_s = ["All media has been downloaded with the following numbers:\n\t"]
            tmp_s += [CN, fmed, CT, "/", CN, tmed, CT, "medias and", CN]
            tmp_s += [falb, CT, "/", CN, talb, CT]
            printInfo(*TMP_I, *tmp_s, "albums has been downloaded", CN)

    def refreshDownloads(self):
        for album_name in self.ultimatum["albums"]:
            self.ultimatum["albums"][album_name]["downloaded"] = []
        for media_name in self.ultimatum["medias"]:
            self.ultimatum["medias"][media_name]["downloaded"] = False

        self.saveUltimatum()
        printInfo(*TMP_I, "All downloaded status got flushed in the json file", CN)

    def resumeDownloads(self):
        if self.ultimatum == {}:
            tmp_s = ["There are no data to download, please harvest links", CE]
            printInfo("!", "red", CA, *tmp_s)
        else:
            self._downloadAll(verbose=False)
