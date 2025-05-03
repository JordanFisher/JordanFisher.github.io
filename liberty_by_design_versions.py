from dataclasses import dataclass


@dataclass
class BookVersion:
    uri: str
    gdoc: str
    description: str


liberty_versions = [
    BookVersion(
        uri="liberty_by_design",
        gdoc="https://docs.google.com/document/d/1-CifFI15IsW5fj4DvSrH9SmpKJbAELyeHTKCfdGT6rs/",
        description="I'm new to AI"
    ),
    BookVersion(
        uri="liberty_by_design_up_to_speed_version",
        gdoc="https://docs.google.com/document/d/17jSp5YFfF2F-U2_vbWpYm7JUoy8iM2Z83WOHv5owuv0/",
        description="I'm up to speed on AI"
    ),
    BookVersion(
        uri="liberty_by_design_agi_pilled_version",
        gdoc="https://docs.google.com/document/d/1zrvgArp4Ulaf71Yz4mnFa9oCEQC5lB_CpVHH5G6bEik/",
        description="I’m up to speed on AI and I think AGI is near"
    ),
]