from threading import BoundedSemaphore, Thread
from time import time
from typing import List, Optional
from json import dumps

from pyrhd.downloader.dler import BaseDownloader
from pyrhd.utility.cprint import aprint, deleteLines, printInfo

from .constants import *
from .utility import Utils as UTL


class Downloader(BaseDownloader):
    def __init__(
        self,
        sub_name: str,
        download_path: str,
        verbose: Optional[str] = "min",
    ):
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
        self.downloadAlbums()
        self.downloadPicsVids()
        # deleteLines(2)
        UTL.threading.joinThreads(self.thr)
        self.saveUltimatum()
        self.printVerbose(2)

    def downloadAlbums(self):
        for album_url, album_info in self.ultimatum["albums"].items():
            media_set = set(album_info["mediaUrls"] if album_info["mediaUrls"] else [])
            downloaded_set = set(
                album_info["downloaded"] if album_info["downloaded"] else []
            )
            diff_list = media_set - downloaded_set
            if diff_list == set():
                continue
            args = [[album_url, album_info, diff_list], self.thr]
            UTL.threading.createThread(self.downloadAnAlbum, *args)

    def downloadAnAlbum(self, album_url: str, album_info: dict, diff_list: set):
        sub_folder = album_info["title"].replace(".", "")[:40].strip()
        __path = f"{self.download_path}\\{sub_folder}"
        UTL.os.makedir(__path)
        for media_url in diff_list:
            self.sema4.acquire()
            if self.downloadMedia(media_url, __path, None, self.sema4, None):
                self.ultimatum["albums"][album_url]["downloaded"].append(media_url)

    def downloadPicsVids(self):
        u_media = self.ultimatum["medias"]
        for parent_url, media_info in u_media.items():
            if u_media[parent_url]["downloaded"]:
                continue
            self.sema4.acquire()
            args = [[parent_url, media_info], self.thr]
            UTL.threading.createThread(self.downloadAPicVid, *args)

    def downloadAPicVid(self, parent_url, media_info):
        title = media_info["title"]
        _id = parent_url.split("-")[-1].strip()
        media_url = media_info["mediaUrl"]
        if self.downloadMedia(media_url, self.download_path, title, self.sema4, _id):
            self.ultimatum["medias"][parent_url]["downloaded"] = True

    def downloadMedia(
        self,
        media_url: str,
        media_path: str,
        title: str,
        sema4: BoundedSemaphore,
        _id: str = None,
    ) -> bool:
        url_filename, ex10sion = media_url.split("/")[-1].split(".")
        ex10sion = ex10sion.split("?")[0] if "?" in ex10sion else ex10sion
        if title:
            title = title.replace(".", "")[:40]
            title = fr"{title}-{_id}.{ex10sion}"
        else:
            url_filename = url_filename.replace(".", "")[:40]
            title = fr"{url_filename}.{ex10sion}"
        if self.downloadAMedia(media_url, media_path, title, sema4, True, False):
            # deleteLines(2)
            # aprint("✅ Downloaded video from", CS, media_url, CU)
            self.printVerbose(1)
            return True
        return False

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
            tmp_s += [falb, CT, "/", CN, talb, CT]
            printInfo(*tmp_s, "albums has been downloaded", CN, same_line=True)
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
        # for s_name, section in self.ultimatum.items():
        #     for c_name, chapter in section["chapters"].items():
        #         for l_url, lecture in chapter.items():
        #             pointer = self.ultimatum[s_name]["chapters"][c_name][l_url]
        #             pointer["dl"] = False

        self.saveUltimatum()
        printInfo(*TMP_I, "All downloaded status got flushed in the json file", CN)

    def resumeDownloads(self):
        if self.ultimatum == {}:
            tmp_s = ["There are no data to download, please harvest links", CE]
            printInfo("!", "red", CA, *tmp_s)
        else:
            self._downloadAll(verbose=False)
