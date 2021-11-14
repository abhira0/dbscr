import enum
import json
from copy import deepcopy
from threading import BoundedSemaphore, Thread
from time import time
from typing import List, Optional

from pyrhd.harvester.hrv8r import BaseHarvester
from pyrhd.utility.cprint import aprint, deleteLines, printInfo

from .constants import *
from .utility import Utils as UTL


class Harvester(BaseHarvester):
    def __init__(
        self,
        download_path: str,
        verbose: Optional[str] = "min",
    ):
        start_time = time()
        if verbose == "info":
            aprint("\n>>>", CA, "Harvester\n", CB)
        tmp_s = ["Harvester", CC, "for", CN, ROOT_URL, CU, "has been instantiated", CN]
        printInfo(*TMP_I, *tmp_s)

        self.download_path = download_path
        ultimatum_path = f"{download_path}\\{BASE_U_PATH}"
        super().__init__(ultimatum_path, 10)
        self.harvest()

        if verbose == "info":
            aprint("\n>>>", CA, "Harvester-End\n", CB)
        tmp_s = ["Time taken for", CN, "Harvester", CC, "class to complete is", CN]
        time_taken = round(time() - start_time, 6)
        printInfo(*TMP_I, *tmp_s, time_taken, CT, "seconds", CN)

    def harvest(self):
        self.setCookies()
        # self.sectionIter()
        self.lectureIter()
        self.saveUltimatum()
        # self.saveErrorLog()

    def setCookies(self):
        c_text = COOKIES.split(";")
        self.cookies = {}
        for i in c_text:
            a, b = map(lambda x: x.strip(), i.split("="))
            self.cookies[a] = b

    def sectionIter(self):
        sections_css = "html > body > div > div > div > div > a"
        printInfo(*TMP_I, "Getting Metadata from the site", CN)
        sections = UTL.requests.sourceCode(BASE_URL, sections_css)
        for i in sections:
            s_name = i.getText()
            s_url = ROOT_URL + i["href"]
            tmp = {"s_url": s_url, "chapters": {}}
            self.ultimatum[s_name] = self.ultimatum.get(s_name, tmp)

        for s_name in self.ultimatum:
            s_url = self.ultimatum[s_name]["s_url"]
            self.getSectionInfo(s_url, s_name)
            tmp_s = [f"Collecting metadata of section named :", CN]
            printInfo(*TMP_I, *tmp_s, s_name, CT, same_line=True)

        tmp_s = ["Metadata of all", CN, len(sections), CT]
        printInfo(*TMP_I, *tmp_s, "sections has been collected", CN)

    def getSectionInfo(self, s_url, s_name):
        cssSel = "html > body > div > div > div > div.col-sm-6"
        hds = UTL.requests.sourceCode(s_url, cssSel)
        chap_name = None
        for i in hds:
            for j in i.children:
                if str(j).startswith("<h4"):
                    chap_name = j.getText()
                elif str(j).startswith("<ul"):
                    for k in j.select("div.lesson-item"):
                        c_poi = self.ultimatum[s_name]["chapters"]

                        tmp = k.select_one("a").getText().strip().split("\n")
                        lec_name = " ~ ".join(tmp)

                        lec_url = ROOT_URL + k.select_one("a")["href"]
                        c_poi[chap_name] = c_poi.get(chap_name, {})

                        tmp = c_poi[chap_name].get(lec_url, {"name": lec_name})
                        c_poi[chap_name][lec_url] = tmp

    def lectureIter(self, page_urls: List[str]):
        # Iterating through all the pages
        thr: List[Thread] = []
        sema4 = BoundedSemaphore(CONF["thread"]["lecture"])
        for url in page_urls:
            sema4.acquire()
            UTL.threading.createThread(self.getLectureInfo, [url, sema4], thr)
        UTL.threading.joinThreads(thr)  # Waiting for threads to terminate

    def getLectureInfo(self, page_url: str, sema4: BoundedSemaphore):
        # Below selector selects the heading containing the title and link for models in a page
        cssSelector = "html > body > div > div > div > div > div > div > div > div > a"
        models_obj = UTL.requests.sourceCode(page_url, cssSelector)
        for model_obj in models_obj:
            href = ROOT_URL + model_obj["href"][1:]
            title = model_obj.select_one("img")["alt"]
            self.ultimatum[href] = self.ultimatum.get(href, {"title": title})
        sema4.release()

    def _get_harvested_album_count(self):
        c = 0
        for model_url in deepcopy(self.ultimatum):
            media_links = self.ultimatum[model_url].get("media_links", [])
            if media_links:
                c += 1
        return c

    def saveErrorLog(self):
        d = {"harvest_urls": self.error_list}
        with open(f"{self.download_path}\\{BASE_L_PATH}", "w") as f:
            json.dump(d, f, indent=4)
