from basicprogressbar import BasicProgressBar

class DiscordProgressBarAsync(BasicProgressBar):
    """
        Send progress bar to discord
        using async (httpx) and time
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

    async def next(self):
        self.current += 1
        await self.send()

    async def send(self):
        import httpx
        import time
        builtbar = self.bar()
        if self.messtime+self.throttle <= time.time() or self.current == self.total:
            client = httpx.AsyncClient()
            webhook = "https://discord.com/api/webhooks/"+self.idtoken
            data = {"content": f"{builtbar}", "username": f"{self.disuser}"}
            if self.messid == "":
                try:
                    resp = await client.post(
                        webhook+"?wait=true", json=data, timeout=self.timeout)
                    if resp.status_code == 200:
                        self.messid = resp.json()['id']
                except:
                    self.messid = ""  # Failed to send message returns blank to try again
            else:
                try:
                    resp = await client.patch(
                        webhook+"/messages/"+self.messid, json=data, timeout=self.timeout)
                except:
                    pass
            self.messtime = time.time()
            await client.aclose()
        return self.messid, self.messtime
