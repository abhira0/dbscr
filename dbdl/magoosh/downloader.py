from threading import BoundedSemaphore, Thread
from time import time
from typing import List, Optional

from pyrhd.downloader.dler import BaseDownloader
from pyrhd.utility.cprint import aprint, deleteLines, printInfo

from .constants import *
from .utility import Utils as UTL


class Downloader(BaseDownloader):
    def __init__(
        self,
        download_path: str,
        verbose: Optional[str] = "min",
    ):
        start_time = time()
        if verbose == "info":
            aprint("\n>>>", CA, "Downloader\n", CB)
        tmp_s = ["Downloader", CC, "for", CN, ROOT_URL, CU, "has been instantiated", CN]
        printInfo(*TMP_I, *tmp_s)

        self.download_path = download_path
        ultimatum_path = f"{download_path}\\{BASE_U_PATH}"
        super().__init__(ultimatum_path, 10)
        self.total_videos = self.getTotalVideosCount()
        self.header = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "DNT": "1",
            "Host": "d296n67kxwq0ge.cloudfront.net",
            "If-Modified-Since": "Thu, 29 Sep 2016 11:15:06 GMT",
            "If-None-Match": "ad84869534a20c303a76966356886735",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "TE": "trailers",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
        }
        self.download()

        if verbose == "info":
            aprint("\n>>>", CA, "Downloader-End\n", CB)
        tmp_s = ["Time taken for", CN, "Downloader", CC, "class to complete is", CN]
        time_taken = round(time() - start_time, 6)
        printInfo(*TMP_I, *tmp_s, time_taken, CT, "seconds", CN)

    def download(self):
        self._downloadAll()
        self.saveUltimatum()
        deleteLines(2)
        printInfo(*TMP_I, "All media has been downloaded", CN)

    def _downloadAll(self, verbose: bool = True):
        aprint("\n")
        sema4 = BoundedSemaphore(CONF["thread"]["download"])
        thr: List[Thread] = []
        db_root = f"{self.download_path}\\{BASE_D_PATH}"
        UTL.os.makedirs(db_root)

        for s_name, section in self.ultimatum.items():
            s_path = f"{db_root}\\{s_name}"  # section path
            UTL.os.makedir(s_path)
            for c_name, chapter in section["chapters"].items():
                path_ = f"{s_path}\\{c_name}"
                UTL.os.makedir(path_)
                for l_url, lecture in chapter.items():
                    sema4.acquire()
                    url = lecture["url"]
                    f_name = lecture["name"] + ".mp4"  # filename
                    f_name = f_name.replace(":", "_")
                    args = [url, path_, f_name, s_name, c_name, l_url, sema4]
                    UTL.threading.createThread(self.downloadAVideo, args, thr)
        UTL.threading.joinThreads(thr)

    def downloadAVideo(
        self,
        url: str,
        dir_: str,
        name: str,
        s_name: str,
        c_name: str,
        l_url: str,
        sema4: BoundedSemaphore,
    ):
        pointer = self.ultimatum[s_name]["chapters"][c_name][l_url]
        if pointer.get("dl", False) == True:
            ...
        else:
            self.downloadAMedia(url, dir_, name, verbose=False)
            pointer["dl"] = True
            deleteLines(2)
            aprint("✅ Downloaded video from", CS, url, CU)
            tot = self.total_videos
            fin = self.get_downloaded_lecture_count()
            tmp_s = [*TMP_I, fin, CT, "out of", CN, tot, CT]
            printInfo(*tmp_s, "has been downloaded", CN)
        sema4.release()

    def getTotalVideosCount(self):
        c = 0
        for s_name, section in self.ultimatum.items():
            for c_name, chapter in section["chapters"].items():
                c += len(chapter)
        return c

    def get_downloaded_lecture_count(self):
        c = 0
        for s_name, section in self.ultimatum.items():
            for c_name, chapter in section["chapters"].items():
                for l_url, lecture in chapter.items():
                    c += lecture.get("dl", False)
        return c

    def refreshDownloads(self):
        for s_name, section in self.ultimatum.items():
            for c_name, chapter in section["chapters"].items():
                for l_url, lecture in chapter.items():
                    pointer = self.ultimatum[s_name]["chapters"][c_name][l_url]
                    pointer["dl"] = False

        self.saveUltimatum()
        printInfo(*TMP_I, "All downloaded status got flushed in the json file", CN)

    def resumeDownloads(self):
        if self.ultimatum == {}:
            tmp_s = ["There are no data to download, please harvest links", CE]
            printInfo("!", "red", CA, *tmp_s)
        else:
            self._downloadAll(verbose=False)
