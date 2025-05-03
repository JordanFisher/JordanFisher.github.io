from dataclasses import dataclass


@dataclass
class Post:
    uris: list[str]
    gdoc_url: str = ""
    url: str = ""
    title: str = ""
    description: str = ""


posts = [
    Post(title="Liberty by Design", uris=["liberty_by_design"], url="https://jordanfisher.github.io/posts/liberty_by_design.html"),

    Post(uris=["superchecks_superbalances"], gdoc_url="https://docs.google.com/document/d/141zqb94MsAcwBFyk-srcTPEtN3dpDzJe6pN0wts_pcM/"),
    Post(uris=["the_prompt_of_power"], gdoc_url="https://docs.google.com/document/d/1VnChDrRDJVqjMwu_kHS1BzhFjpn37ryNrRWZdaRUUxc/"),
    Post(uris=["implicit_guardrails"], gdoc_url="https://docs.google.com/document/d/1YSvUWGOTsk521pFGTIoaw6o375P-Hl5yDnh15dQ9MGg/"),
    Post(uris=["by_any_other_name"], gdoc_url="https://docs.google.com/document/d/1zyN6ZNIWZx3qaPK3PPOd7H8wyW_LsxytOD7t7T8OTag/"),
    Post(uris=["rapid_fire_governance"], gdoc_url="https://docs.google.com/document/d/1vpDT4RJpSOw_vdGMdIv52l1zW7flywl9oqSMm6yPTW8/"),
    Post(uris=["if_you_can_keep_it"], gdoc_url="https://docs.google.com/document/d/1zG0-u7hqdocWZAdLpTae0aaapAV41fgSFD9jUmjGxyI/"),
    Post(uris=["why_ai_is_accelerating"], gdoc_url="https://docs.google.com/document/d/1IV4hKVDoEgA5EZvDRfAtviDI0Stpj0m8MIEVPdLtLV4/"),
    Post(uris=["the_real_politik"], gdoc_url="https://docs.google.com/document/d/1rB0LTHYm4icUP0BCbc56X1VX9Oge5dTMQ8n0laPxi4Q/"),

    Post(uris=["please_be_silly"], gdoc_url="https://docs.google.com/document/d/1jKHxIXSFW1zwqVCSuRiTz8_svEtRXSaXqST-SAVe9_U/"),
    Post(uris=["concrete"], gdoc_url="https://docs.google.com/document/u/0/d/1c4bZTcHbjBJdIlbq9vmxS53SH04WQ__S-sSRNqXcLRg/"),
    Post(uris=["complexity_and_design"], gdoc_url="https://docs.google.com/document/d/1tgyr9L9hymcLlVvgkkF1Bfrho_DWo7jkW8--AeQi2K8/"),
    Post(uris=["crash_course_on_ai"], gdoc_url="https://docs.google.com/document/d/1g1MrziAeRAOkppKQvBdSgGJqC5d-pr4F5-i1mcRNJGQ/edit?tab=t.0"),

    # Include these only if you want to analyze the documents. Normally these are excluded, as they are just components of the bigger Liberty book.
    # Post(uris=["liberty_by_design"], gdoc_url="https://docs.google.com/document/d/1-CifFI15IsW5fj4DvSrH9SmpKJbAELyeHTKCfdGT6rs/"),
    # Post(uris=["what_we_want_from_governance"], gdoc_url="https://docs.google.com/document/d/1gYJiFmj8k_DVFAE31GPMe74mrSNUzLuler7wlHy5aco/"),
    # Post(uris=[""], gdoc_url=""),
]