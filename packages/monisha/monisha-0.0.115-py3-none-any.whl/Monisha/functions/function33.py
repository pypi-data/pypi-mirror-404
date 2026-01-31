import pytz
from datetime import datetime
#===============================================================================

class SchedulER:

    @staticmethod
    async def get20():
        nowaes = datetime.now(tz=pytz.timezone("Asia/Kolkata"))
        mineed = nowaes.replace(hour=0, minute=0, second=0, microsecond=0)
        return (mineed - nowaes).seconds

#===============================================================================

class Schedules:

    def __init__(self, **kwargs):
        self.moon01 = kwargs.get("hours", 0)
        self.moon02 = kwargs.get("minutes", 0)
        self.moon03 = kwargs.get("seconds", 0)
        self.moon04 = kwargs.get("microsecond", 0)
        self.moon05 = kwargs.get("zone", "Asia/Kolkata")

    def get01(self):
        nowaes = datetime.now(tz=pytz.timezone(self.moon05))
        mineed = nowaes.replace(hour=self.moon01, minute=self.moon02,
                                second=self.moon03, microsecond=self.moon04)
        return (mineed - nowaes).seconds

    async def get02(self):
        nowaes = datetime.now(tz=pytz.timezone(self.moon05))
        mineed = nowaes.replace(hour=self.moon01, minute=self.moon02,
                                second=self.moon03, microsecond=self.moon04)
        return (mineed - nowaes).seconds

#===============================================================================
