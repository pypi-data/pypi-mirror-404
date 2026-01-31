"""
    Basic progress bar
"""
import time


class BasicProgressBar:
    """
        Basic progress bar
    """

    def __init__(self,
                 current: float = 0,
                 total: float = -1,
                 posttext: str = "",
                 pretext: str = "Progress:",
                 length: int = 60,
                 endtext: str = "",
                 endline: str = '\r',
                 showtimer=False):

        self.current = current
        self.total = total
        self.posttext = posttext
        self.pretext = pretext
        self.length = length
        self.endtext = endtext
        self.endline = endline
        self.barfill = None
        self.percent = None
        self.remainingtime = ""
        self.showtimer = showtimer
        if self.showtimer:
            import time
            self.timerlist = []

    def buildbar(self):
        """
            Generate Progress Bar
        """

        if self.showtimer:
            """
                timer calculations
            """
            
            self.timerlist.append(time.time())
            while len(self.timerlist) > 10:
                self.timerlist.pop(0)
            avgtime = 0
            for i in self.timerlist:
                avgtime += i
            if len(self.timerlist) > 2:
                diff = round(sum([self.timerlist[i+1]-self.timerlist[i]
                             for i in range(len(self.timerlist)-1)])/(len(self.timerlist)-1), 2)
                diff = int(round(diff*(self.total-self.current), 0))
                try:
                    import secondstotext
                    self.remainingtime = " " + str(secondstotext.Sectxt(diff))
                except:
                    self.remainingtime = " " + str(diff) + ' Seconds'

        if self.total == -1:  # endless progress bar
            if self.barfill == None or self.barfill[0] == "█":
                barchar = "░██░"
            else:
                barchar = "█░░█"
            self.barfill = barchar*int(self.length/4)
            return f"{self.pretext} {self.barfill} [{self.current}] {self.posttext}"
        else:
            self.percent = int((self.current/self.total)*100)
            barlen = int(self.percent/100*self.length)
            self.barfill = "█"*barlen+"░"*(self.length-barlen)
            if self.total == self.current:  # bar is full
                self.endline = '\n'  # newline at end when bar is full
                self.remainingtime = ""
                if self.endtext != "":
                    self.posttext = self.endtext+" " * \
                        (len(str(self.posttext))-len(str(self.endtext)))
                    # add space to posttext if it is shorter than endtext
            return f"{self.pretext} {self.barfill} {self.percent}% [{self.current}/{self.total}]{' ' + self.posttext if self.posttext else ''}{self.remainingtime}"

    def bar(self, printbar: bool = False):
        """
            Print or return Progress Bar
        """
        if printbar:
            print(self.buildbar(), end=self.endline)
        else:
            return self.buildbar()

    def next(self, printbar: bool = False):
        """
            Increment current by 1, return or print progress bar
        """
        self.current += 1
        if printbar:
            self.bar(True)
        else:
            return self.buildbar()
