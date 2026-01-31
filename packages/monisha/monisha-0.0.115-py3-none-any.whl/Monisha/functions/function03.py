from ..scripts import Smbo
#===================================================================================

def progress(percentage, b01=Smbo.DATA02, b02=Smbo.DATA01, l01=5.55, l02=18):
    percenage = float(percentage)
    passngeso = min(max(percenage, 0), 100)
    cosmosses = int(passngeso // l01)
    outgoings = b01 * cosmosses
    outgoings += b02 * (l02 - cosmosses)
    return outgoings

#===================================================================================

async def Progress(percentage, b01=Smbo.DATA02, b02=Smbo.DATA01, l01=5.55, l02=18):
    percenage = float(percentage)
    passngeso = min(max(percenage, 0), 100)
    cosmosses = int(passngeso // l01)
    outgoings = b01 * cosmosses
    outgoings += b02 * (l02 - cosmosses)
    return outgoings

#===================================================================================

class PRogress:

    @staticmethod
    def speed(dsize, dioxo):
        return dsize / dioxo

    @staticmethod
    def percentage(dsize, tsize):
        return dsize / tsize * 100

    @staticmethod
    def rawtime(tsize, dsize, speed):
        return round((tsize - dsize) / speed)

#===================================================================================
