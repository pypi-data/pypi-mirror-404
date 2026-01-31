from basicprogressbar import BasicProgressBar

class DiscordProgressBar(BasicProgressBar):
    """
        Send progress bar to discord
        depends on requests and time
    """

    def __init__(self,
                 current: float = 0,
                 total: float = -1,
                 idtoken: str = "",
                 disuser: str = "Progress Bar",
                 throttle: float = 0.5,
                 messtime: float = 0.0,
                 messid: str = "",
                 timeout: float = 10.0,
                 **kwargs):

        super().__init__(current, total, **kwargs)

        self.idtoken = idtoken
        self.disuser = disuser
        self.throttle = throttle
        self.messtime = messtime
        self.messid = messid
        self.timeout = timeout

    def next(self):
        self.current += 1
        self.send()

    def send(self):
        import requests
        import time
        builtbar = self.bar()
        if self.messtime+self.throttle <= time.time() or self.current == self.total:
            webhook = "https://discord.com/api/webhooks/"+self.idtoken
            data = {"content": f"{builtbar}", "username": f"{self.disuser}"}
            if self.messid == "":
                try:
                    resp = requests.post(
                        webhook+"?wait=true", json=data, timeout=self.timeout)
                    if resp.status_code == 200:
                        self.messid = resp.json()['id']
                except:
                    self.messid = ""  # Failed to send message returns blank to try again
            else:
                try:
                    resp = requests.patch(
                        webhook+"/messages/"+self.messid, json=data, timeout=self.timeout)
                except:
                    pass
            self.messtime = time.time()
        return self.messid, self.messtime
