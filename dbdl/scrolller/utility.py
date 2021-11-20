import re
import time

from pyrhd import Utils
from pyrhd.utility.cprint import aprint


class Utils(Utils):
    @staticmethod
    def cleanURL(url: str):
        rep = re.findall(r"[-]\d{3}[x]\d{3}[\.]", url)
        if rep != []:
            url = url.replace(rep[0], ".")  # Changing the resolution
        return url

    @staticmethod
    def tryWait(
        function_name,
        argz: list,
        timeout: int,
        desc: str = None,
        verbose=True,
    ):
        """[summary]

        Args:
            function_name (function): The function object which needed to be tried
            argz (list): The arguments that must be passed to the function
            timeout (int): Maximum timeout in seconds
            desc (str): Description that needed to be printed inside the verbose line
            verbose (bool, optional): Boolean value which turns the verbose mode on. Defaults to True.

        Returns:
            object: Any object returned by the function
        """
        for _ in range(timeout):
            try:
                return_objs = function_name(*argz)
                if return_objs:
                    return return_objs
                else:
                    time.sleep(1)
            except:
                time.sleep(1)
        if verbose:
            aprint(f"❗ Function execution failed for '{desc}' @ {function_name}", "red")

    # Tries for given time and returns the return_object on success
    @staticmethod
    def tryExcept(function_name, argz: list, timeout: int, desc=None, verbose=True):
        """Tries for given time and returns tries_left on success"""
        for i in range(timeout):
            try:
                function_name(*argz)
                return timeout - i - 1
            except:
                time.sleep(1)
        if verbose:
            aprint(f"❗ Function execution failed for '{desc}' @ {function_name}", "red")
