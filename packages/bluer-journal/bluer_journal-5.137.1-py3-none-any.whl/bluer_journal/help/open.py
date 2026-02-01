from typing import List

from bluer_options.terminal import show_usage


def help_open(
    tokens: List[str],
    mono: bool,
) -> str:
    options = "code|web,page=latest|<page-name>"

    return show_usage(
        [
            "@journal",
            "open",
            f"[{options}]",
        ],
        "open journal.",
        mono=mono,
    )
