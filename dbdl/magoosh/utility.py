import re
from datetime import datetime

from pyrhd.utility.utils import Utils


class Utils(Utils):
    @staticmethod
    def cleanURL(url: str):
        rep = re.findall(r"[-]\d{3}[x]\d{3}[\.]", url)
        if rep != []:
            url = url.replace(rep[0], ".")  # Changing the resolution
        return url
