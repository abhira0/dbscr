import json
from threading import BoundedSemaphore, Thread
from time import time
from typing import List, Optional
import requests

from pyrhd.harvester.hrv8r import BaseHarvester
from pyrhd.utility.cprint import aprint, printInfo

from .constants import *
from .utility import Utils as UTL


class Harvester(BaseHarvester):
    def __init__(
        self,
        sub_name: str,
        download_path: str,
        verbose: Optional[str] = "min",
    ):
        start_time = time()
        if verbose == "info":
            aprint("\n>>>", CA, "Harvester\n", CB)
        tmp_s = ["Harvester", CC, "for", CN, f"{ROOT_URL}r/{sub_name}", CU]
        tmp_s += ["has been instantiated", CN]
        printInfo(*TMP_I, *tmp_s)

        self.post_url = "https://api.scrolller.com/api/v2/graphql"
        self.ultimatum = {"albums": {}, "medias": {}}
        self.sub_name = sub_name
        self.media_len = len(self.ultimatum["medias"])
        self.album_len = len(self.ultimatum["albums"])
        self.album_media_len = sum(
            i["mediaUrls"] != [] for i in self.ultimatum["albums"].values()
        )

        self.download_path = download_path
        ultimatum_path = f"{download_path}\\{BASE_PATH}\\{sub_name}\\{sub_name}.json"
        super().__init__(ultimatum_path, SAVING_INTERVAL, self.ultimatum)
        self.harvest()

        if verbose == "info":
            aprint("\n>>>", CA, "Harvester-End\n", CB)
        tmp_s = ["Time taken for", CN, "Harvester", CC, "class to complete is", CN]
        time_taken = round(time() - start_time, 6)
        printInfo(*TMP_I, *tmp_s, time_taken, CT, "seconds", CN)
        self.quitSaver()

    def harvest(self):
        tmp_s = ["Started collection of all the medias for:", CN, self.sub_name, CT]
        printInfo(*TMP_I, *tmp_s)
        self.threadSubreddit()
        self.threadSubreddit()
        self.threadAlbums()
        self.printVerbose(3)
        self.saveUltimatum()

    def threadSubreddit(self) -> None:
        self.stop_quering = max(CONF["reset"]["query"], len(self.ultimatum["medias"]))
        sema4 = BoundedSemaphore(CONF["thread"]["media"])
        thr: List[Thread] = []
        while True:
            sema4.acquire()
            if self.stop_quering <= 0:
                break
            UTL.threading.createThread(self.processSubResponse, [sema4], thr)
        UTL.threading.joinThreads(thr)

    def processSubResponse(self, sema4: BoundedSemaphore) -> None:
        children_items = self.querySubreddit()
        new_entity = 0
        for child in children_items:
            albumUrl, url = child["albumUrl"], child["url"]
            title = UTL.os.cleanPathName(child["title"])
            if albumUrl and (albumUrl not in self.ultimatum["albums"].keys()):
                tmp_dict = {"title": title, "mediaUrls": [], "downloaded": []}
                self.ultimatum["albums"][albumUrl] = tmp_dict
                new_entity += 1
                self.album_len += 1
            elif url not in self.ultimatum["medias"].keys():
                mediaUrl = child["mediaSources"][-1]["url"]
                tmp_dict = {"title": title, "mediaUrl": mediaUrl, "downloaded": False}
                self.ultimatum["medias"][url] = tmp_dict
                new_entity += 1
                self.media_len += 1
        self.printVerbose(1)
        if new_entity == 0:
            self.stop_quering -= len(children_items)
        else:
            maxi = max(CONF["reset"]["query"], len(self.ultimatum["medias"]))
            self.stop_quering = maxi
        sema4.release()

    def querySubreddit(self):
        __subreddit_query = {
            "query": "query SubredditQuery( $url: String! $filter: SubredditPostFilter $iterator: String $hostsDown: [HostDisk] ) { getSubreddit(url: $url) { children( limit: 50 iterator: $iterator filter: $filter disabledHosts: $hostsDown ) { iterator items { __typename url title subredditTitle subredditUrl redditPath isNsfw albumUrl isFavorite mediaSources { url width height isOptimized } } } } }",
            "variables": {"url": f"/r/{self.sub_name}", "filter": None},
            "authorization": None,
        }
        response_obj = requests.post(self.post_url, json=__subreddit_query)
        response_json = json.loads(response_obj.text)
        children_items = response_json["data"]["getSubreddit"]["children"]["items"]
        return children_items

    def threadAlbums(self) -> None:
        sema4 = BoundedSemaphore(CONF["thread"]["album"])
        thr: List[Thread] = []
        for album_url in self.ultimatum["albums"].keys():
            sema4.acquire()
            args = [album_url, sema4]
            UTL.threading.createThread(self.processAlbResponse, args, thr)
        UTL.threading.joinThreads(thr)

    def processAlbResponse(self, album_url: str, sema4: BoundedSemaphore) -> None:
        children_items = self.queryAlbum(album_url)
        media_link_list = [i["mediaSources"][-1]["url"] for i in children_items]
        self.ultimatum["albums"][album_url]["mediaUrls"] = media_link_list
        self.album_media_len += 1
        self.printVerbose(2)
        sema4.release()

    def queryAlbum(self, album_url: str):
        __album_query = {
            "query": "query AlbumQuery( $url: String! $iterator: String ) { getAlbum(url: $url) { __typename url title isComplete isNsfw redditPath children( iterator: $iterator limit: 50 ) { iterator items { __typename mediaSources { url width height isOptimized } } } } }",
            "variables": {"url": album_url},
            "authorization": None,
        }
        response_obj = requests.post(self.post_url, json=__album_query)
        response_json = json.loads(response_obj.text)
        children_items = response_json["data"]["getAlbum"]["children"]["items"]
        return children_items

    def printVerbose(self, stage: int = 1) -> None:
        self.media_len = len(self.ultimatum["medias"])
        p = self.ultimatum["albums"]
        self.album_len = len(p)
        if self.album_len != 0:
            self.album_media_len = 0
            for i, j in p.items():
                if j.get("mediaUrls", []) != []:
                    self.album_media_len += 1
        if stage == 1:
            # just harvest subreddit page
            tmp_s = ["Medias:", CN, self.media_len, CT, "Albums:", CN]
            tmp_s += [self.album_len, CT]
            printInfo(*TMP_I, *tmp_s, same_line=True)
        elif stage == 2:
            # after harvesting subreddit page, harvest album pages
            tmp_s = ["Medias:", CN, self.media_len, CT, "Albums:", CN]
            tmp_s += [self.album_len, CT, "Parsed Albums:", CN]
            tmp_s += [self.album_media_len, CT]
            printInfo(*TMP_I, *tmp_s, same_line=True)
        elif stage == 3:
            tmp_s = ["Harvesting complete with the following numbers\n", CN]
            tmp_s += ["\tMedias:", CN, self.media_len, CT, "Albums:", CN]
            tmp_s += [self.album_len, CT, "Parsed Albums:", CN]
            tmp_s += [self.album_media_len, CT]
            printInfo(*TMP_I, *tmp_s)
