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
        if not self.setCookies():
            return False
        self.sectionIter()
        self.lectureIter()
        self.saveUltimatum()

    def setCookies(self) -> bool:
        if COOKIES == "":
            printInfo(*TMP_E, "Please add user-cookie inside constants.py", CE)
            return False

        c_text = COOKIES.split(";")
        self.cookies = {}
        for i in c_text:
            a, b = map(lambda x: x.strip(), i.split("="))
            self.cookies[a] = b
        return True

    def sectionIter(self):
        sections_css = "html > body > div > div > div > div > a"
        printInfo(*TMP_I, "Getting Metadata of sections from the site", CN)
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

    def lectureIter(self):
        thr: List[Thread] = []
        printInfo(*TMP_I, "Getting Metadata of all the lectures", CN)
        sema4 = BoundedSemaphore(CONF["thread"]["lecture"])
        for s_name, section in self.ultimatum.items():
            for c_name, chapters in section["chapters"].items():
                for l_url in chapters:
                    sema4.acquire()
                    args = [l_url, s_name, c_name, sema4]
                    UTL.threading.createThread(self.getLectureInfo, args, thr)
        UTL.threading.joinThreads(thr)
        tmp_s = ["Completed Harvesting of all lectures", CN]
        printInfo(*TMP_I, *tmp_s)

    def getLectureInfo(self, l_url, s_name, c_name, sema4: BoundedSemaphore):
        try:
            l_poi = self.ultimatum[s_name]["chapters"][c_name][l_url]
            l_poi["url"] = l_poi.get("url", None)
            if l_poi["url"] == None:
                cssSel = "html > body > div > div > div > div > div"
                x = UTL.requests.sourceCode(l_url, cssSel, cookies=self.cookies)
                x = x[0]["data-react-props"]
                x = json.loads(x)
                st_url = m_url = None
                for i in x["options"]["sources"]:
                    if i["type"] == "video/mp4":
                        m_url = i["src"]
                if m_url == None:
                    for i in x["options"]["sources"]:
                        if i["type"] == "video/webm":
                            m_url = i["src"]
                for i in x["options"]["tracks"]:
                    if i["label"] == "English":
                        st_url = i["src"]

                l_poi["url"] = m_url
                l_poi["subtitle"] = st_url
                tmp_s = ["Fetched url from:", CN, l_url, CT]
            else:
                tmp_s = ["Existing url from:", CW, l_url, CT]
        except Exception as e:
            printInfo(*TMP_E, e, CE, "for url:", CN, l_url, CU)

        printInfo(*TMP_I, *tmp_s, same_line=True)
        sema4.release() if sema4 else None
