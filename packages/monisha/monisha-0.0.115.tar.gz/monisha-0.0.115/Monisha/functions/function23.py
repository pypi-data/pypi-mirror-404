import re
from ..scripts import Scripted
from .function12 import Regexs
#====================================================================================

class Regexd:

    @staticmethod
    def get01(moonus: str) -> str:
        if not moonus:
            return Scripted.DATA01
        moonus = re.sub(Regexs.DATA12, ' ', moonus)
        moonus = re.sub(Regexs.DATA11, ' ', moonus)
        return moonus.strip()

#====================================================================================

    @staticmethod
    def get02(moonus: str) -> str:
        if not moonus:
            return Scripted.DATA01
        moonus = re.sub(Regexs.DATA13, ' ', moonus)
        moonus = re.sub(Regexs.DATA11, ' ', moonus)
        return moonus.strip()

#====================================================================================

    @staticmethod
    def get03(moonus: str, *, lower: bool = True) -> str:
        if not moonus:
            return Scripted.DATA01
        moonus = Regexs.DATA21.sub('', moonus)
        moonus = Regexs.DATA22.sub(' ', moonus)
        moonus = re.sub(Regexs.DATA12, ' ', moonus)
        moonus = re.sub(Regexs.DATA14, ' ', moonus)
        moonus = re.sub(Regexs.DATA11, ' ', moonus)
        moonus = moonus.lower() if lower else moonus
        return moonus.strip()

#====================================================================================

    @staticmethod
    def get04(moonus: str) -> str:
        if not moonus:
            return Scripted.DATA01
        moonus = re.sub(Regexs.DATA12, ' ', moonus)
        moonus = re.sub(Regexs.DATA31, ' ', moonus, flags=re.IGNORECASE)
        moonus = re.sub(Regexs.DATA32, ' ', moonus, flags=re.IGNORECASE)
        moonus = re.sub(Regexs.DATA33, ' ', moonus, flags=re.IGNORECASE)
        moonus = re.sub(Regexs.DATA34, ' ', moonus, flags=re.IGNORECASE)
        moonus = re.sub(Regexs.DATA35, ' ', moonus, flags=re.IGNORECASE)
        moonus = re.sub(Regexs.DATA36, ' ', moonus, flags=re.IGNORECASE)
        moonus = re.sub(Regexs.DATA38, ' ', moonus)
        moonus = re.sub(Regexs.DATA39, ' ', moonus)
        moonus = re.sub(Regexs.DATA11, ' ', moonus)
        return moonus.strip()

#====================================================================================
