from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SubtitleGroup(Enum):
    LoliHouse = "https://acg.rip/user/1917"
    樱都字幕组 = "https://acg.rip/user/2996"
    桜都字幕组 = "https://acg.rip/user/2996"
    黒ネズミたち = "https://acg.rip/user/5570"
    千夏字幕组 = "https://acg.rip/team/132"
    悠哈璃羽 = "https://acg.rip/team/134"
    喵萌奶茶屋 = "https://acg.rip/team/147"
    拨雪寻春 = "https://acg.rip/team/169"
    ANi = "https://acg.rip/team/173"
    北宇治字幕组 = "https://acg.rip/team/185"
    猎户发布组 = "https://acg.rip/team/191"
    三明治摆烂组 = "https://acg.rip/team/203"
    三明治擺爛組 = "https://acg.rip/team/203"
    绿茶字幕组 = "https://acg.rip/team/212"


@dataclass
class BangumiInfo:
    titles: list[str]
    episode: str
    languages: list[str]
    pub_date: datetime
    link: str
    torrent: str
    group: str | None = None
