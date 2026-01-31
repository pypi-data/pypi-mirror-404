from os import environ
from pathlib import Path
from base64 import b64encode
from json import loads
import asyncio
from asyncio import Queue, Task, TaskGroup
try:
    import requests
except ImportError:
    print("You need requests to send or receive messages via the rest endpoints!")
try:
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed
except ImportError:
    print("You need to install websockets to receive messages from the websocket!")

from messages import MessageParser, Preview


class SignalInterface:
    def __init__(self, port=8080) -> None:
        self.port = port

class SignalRestInterface(SignalInterface):
    def __init__(self, port=8080) -> None:
        super().__init__(port)
        self.signal_account = environ["SIGNAL_ACCOUNT"]
        self.host= "localhost"
        self.url = f"http://localhost:{self.port}"

class RestReceiver(SignalRestInterface):
    def __init__(self, attachment_folder: Path = Path("."),port=8080):
        super().__init__(port)
        self.attc_folder = attachment_folder

    def _get_data(self) -> list[dict]:
        """Get new message data from endpoint and convert it to dict"""
        api_call = "/v1/receive/"
        res_str = requests.get(self.url + api_call + self.signal_account).text
        res_list = loads(res_str)
        return res_list

    def download(self, aid: str) -> Path:
        api_call = f"/v1/attachment/{aid}"
        requests.get(self.url + api_call + self.signal_account)
        return self.attc_folder / aid

    def receive(self) -> list:
        raw_data = self._get_data()
        return [MessageParser(_).parse() for _ in raw_data]

class Transmitter(SignalRestInterface):
    api_call = "/v2/send"
    headers = {"Content-Type": "application/json"}

    def __init__(self, port=8080) -> None:
        super().__init__(port)
        self.send_url = self.url + self.api_call

    @classmethod
    def convert_binary_to_b64(cls, _bytes) -> str:
        return str(b64encode(_bytes), encoding="utf-8")

    @classmethod
    def convert_path_to_b64(cls, fpath) ->str:
        with open(fpath, "rb") as fb:
            b64attachment = cls.convert_binary_to_b64(fb.read())
        return b64attachment

    @classmethod
    def convert_str_to_path(cls, fpathstring: str) -> Path:
        return Path(fpathstring)

    @staticmethod
    def check_url_in_message(msg, url) -> bool:
        if msg in url:
            return True
        return False


    def send_message(
            self,
            receiver_account: list[str],
            msg="",
            attachments: list[Path|str] | None = None,
            preview: Preview | None = None,
    ):
        if attachments and preview:
            print("Can't send message with attachments and preview!")
            return False

        ddict = {
            "message": msg,
            "number": self.signal_account,
            "recipients": receiver_account,
        }

        if attachments:
            b64attachments = []
            for attachment in attachments:
                if isinstance(attachment, str):
                    attachment = self.convert_str_to_path(attachment)
                b64attachments.append(self.convert_path_to_b64(attachment))

            ddict.update({"base64_attachments": b64attachments})

        elif preview:
            if not self.check_url_in_message(msg, preview.url):
                ddict["message"] += f"\n{preview.url}"
            # noinspection PyTypeChecker
            ddict.update(
                {"link_preview": {"url": preview.url, "title": preview.title, "description": preview.description}
                 }
            )
            if preview.filepath:
                if isinstance(preview.filepath, str):
                    preview.filepath = self.convert_str_to_path(preview.filepath)
                b64img = self.convert_path_to_b64(preview.filepath)
                # noinspection PyUnresolvedReferences
                ddict["link_preview"].update({"base64_thumbnail": b64img})
        res = requests.post(self.send_url, headers=self.headers, json=ddict)
        if res.status_code == 201:
            return True
        else:
            raise SyntaxError

class SocketReceiver:

    @staticmethod
    async def receive(signal_account:str,q:Queue, port:int=8080):
        try:
            print("Trying to connect to websocket...")
            async for websocket in connect(f"ws://localhost:{port}/v1/receive/{signal_account}", open_timeout=5):
                    print("Connected to websocket, start receiving....")
                    while True:
                        try:
                            async for message in websocket:
                                print("Received Message!")
                                await q.put(message)
                        except ConnectionClosed:
                            print("Lost connection trying to reconnect....")
                            break
                        except asyncio.CancelledError:
                            websocket.close()
                            return
        except Exception as e:
            print(e)

async def receive_from_socket(q:Queue, port=8080):
    signal_account = environ["SIGNAL_ACCOUNT"]
    await SocketReceiver().receive(signal_account,q, port)

