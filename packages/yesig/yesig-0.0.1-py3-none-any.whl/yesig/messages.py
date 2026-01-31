from dataclasses import dataclass
from pathlib import Path


@dataclass
class Preview:
    url: str
    title: str
    description: str | None
    filepath: Path | None


@dataclass
class ReceivedAttachment:
    contentType: str | None
    filename: str | None
    aid: str | None
    size: int | None
    truepath: Path | None = None

    def __repr__(self):
        return f"[Attachment]\nContentType: {self.contentType}\nFilename: {self.filename}\nAID: {self.aid}\nSize: {self.size}\nTruepath: {self.truepath}"


@dataclass
class ReceivedPreview:
    timestamp: int
    source: str
    name: str
    device: int
    content: str
    url: str
    title: str | None
    description: str | None
    image: ReceivedAttachment | str | None

    def __repr__(self):
        return f"[Preview]From: {self.name} ({self.source})\nDevice: {self.device}\nTime: {self.timestamp}\nTitle: {self.title}\nUrl: {self.url}\nDescription: {self.description}\nContent:{self.content}\nImage: {self.image}"


@dataclass
class ReceivedMessage:
    timestamp: int
    source: str
    name: str
    device: int
    content: str
    attachments: list[ReceivedAttachment] | None

    def __repr__(self):
        return f"[Message]\nFrom: {self.name} ({self.source})\nDevice: {self.device}\nTime: {self.timestamp}\nContent: \n{self.content} \nAttachments: {self.attachments}"


@dataclass
class ReceiptMessage:
    timestamp: int
    source: str
    name: str
    device: int
    when: int
    status: str

    def __repr__(self):
        return f"[Receipt]\nFrom: {self.name} ({self.source})\nTime: {self.timestamp}\nStatus: {self.status}\nWhen: {self.when}"

    def __str__(self):
        return ""


@dataclass
class ReceivedUnkownType:
    timestamp: int
    source: str
    name: str
    device: int
    raw: dict


class MessageParser:
    MSGTYPES = {"dataMessage", "receiptMessage"}

    def __init__(self, received_data_dict: dict):
        self.meta = received_data_dict["envelope"]
        self._set_timestamp()
        self._set_source()
        self._set_dev()
        self._set_name()

    def _set_timestamp(self):
        self.timestamp = self.meta["timestamp"]

    def _set_source(self):
        self.source = self.meta["source"]

    def _set_dev(self):
        self.dev = self.meta["sourceDevice"]

    def _set_name(self):
        self.name = self.meta["sourceName"]

    def _parse_rp(self, dkey) -> ReceiptMessage:
        def _parse_status():
            if data["isDelivery"] is True:
                status = "delivered"
            elif data["isRead"] is True:
                status = "red"
            elif data["isViewed"] is True:
                status = "viewed"
            else:
                status = "undelivered"
            return status

        def _parse_when():
            return data["when"]

        data = self.meta[dkey]

        status = _parse_status()
        when = _parse_when()

        return ReceiptMessage(
            self.timestamp, self.source, self.name, self.dev, when, status
        )

    def _parse_dm(self, dkey) -> ReceivedPreview | ReceivedMessage:
        def _check_preview() -> bool:
            if "previews" in data:
                return True
            return False

        def _parse_preview() -> ReceivedPreview:
            def _parse_preview_attachment():
                if pv["image"] is False:
                    return None
                else:
                    img = pv["image"]

                content_type = img["contentType"]
                aid = img["id"]
                size = img["size"]
                return ReceivedAttachment(content_type, None, aid, size)

            pv = data["previews"]
            url = pv["url"]
            title = pv["title"]
            description = pv["description"]
            image = _parse_preview_attachment()

            return ReceivedPreview(
                self.timestamp,
                self.source,
                self.name,
                self.dev,
                data["message"],
                url,
                title,
                description,
                image,
            )

        def _check_attachments() -> bool:
            if "attachments" in data:
                return True
            return False

        def _parse_attachments() -> list[ReceivedAttachment]:
            attachments = []
            for attchment in data["attachments"]:
                content_type = attchment["contentType"]
                aid = attchment["id"]
                size = attchment["size"]
                filename = attchment["filename"]
                attachments.append(
                    ReceivedAttachment(content_type, filename, aid, size)
                )
            return attachments

        data = self.meta[dkey]
        content = data["message"]
        attachments = None
        if _check_preview():
            return _parse_preview()
        if _check_attachments():
            attachments = _parse_attachments()

        return ReceivedMessage(
            self.timestamp,
            self.source,
            self.name,
            self.dev,
            content,
            attachments,
        )

    def _parse_unkown(self) -> ReceivedUnkownType:
        return ReceivedUnkownType(
            self.timestamp, self.source, self.name, self.dev, self.meta
        )

    def _parse_message(self) -> ReceiptMessage | ReceivedMessage | ReceivedPreview:
        rm = "receiptMessage"
        dm = "dataMessage"
        if rm in self.meta:
            return self._parse_rp(rm)
        elif dm in self.meta:
            return self._parse_dm(dm)
        else:
            raise NotImplementedError

    def parse(
        self,
    ) -> ReceiptMessage | ReceivedPreview | ReceivedMessage | ReceivedUnkownType:
        try:
            msg = self._parse_message()
            return msg
        except NotImplementedError:
            return self._parse_unkown()
