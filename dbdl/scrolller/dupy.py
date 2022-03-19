from pyrhd.postproc.dupy import Dupy as DUPY
from .constants import BASE_PATH
import os


class Dupy:
    def __init__(self, download_path, relative: bool = False) -> None:
        if relative:
            self.download_path = f"{download_path}\\{BASE_PATH}"
        else:
            self.download_path = download_path
        self.du = DUPY(self.download_path)
        self.printCount()
        self.main()
        self.remove_empty_folders()

    def printCount(self):
        x = self.du.getDups()
        c = sum(len(i) for i in x)
        print(c, len(x))

    def main(self):
        for i in self.du.getDups():
            if self.same_dir(i):
                for del_file in i[1:]:
                    os.remove(del_file)
                    ...
            else:
                hm = {}
                for del_file in i:
                    par = os.path.dirname(del_file)
                    hm[par] = hm.get(par, []) + [del_file]
                maxi = ((t := list(hm.keys())[0]), len(t))
                for a in hm:
                    if maxi[1] < len(hm[a]):
                        maxi = (a, len(hm[a]))
                for a in hm[maxi[0]][1:]:
                    os.remove(a)
                hm.pop(maxi[0])
                for a in hm:
                    for del_file in hm[a]:
                        os.remove(del_file)
                        ...

    def same_dir(self, l):
        a = os.path.dirname(l[0])
        for i in l:
            if os.path.dirname(i) != a:
                return False
        return True

    def remove_empty_folders(self):
        walk = list(os.walk(self.download_path))[1:]

        for folder in walk:
            # folder example: ('FOLDER/3', [], ['file'])
            if not folder[2]:
                try:
                    os.rmdir(folder[0])
                except Exception as e:
                    # print(e)
                    ...
