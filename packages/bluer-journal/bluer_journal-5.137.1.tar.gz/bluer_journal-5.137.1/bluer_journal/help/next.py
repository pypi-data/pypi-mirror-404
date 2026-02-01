from typing import List

from bluer_options.terminal import show_usage, xtra

from bluer_journal.help.sync import args as sync_args
from bluer_journal.help.git import push_options


def help_next(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra("~open", mono=mono)

    args = sorted(
        [
            "[--sync 0]]",
        ]
        + sync_args
    )

    return show_usage(
        [
            "@journal",
            "next",
            "[<title>]",
            f"[{options}]",
            "[{}]".format(
                push_options(
                    cascade=True,
                    mono=mono,
                )
            ),
        ]
        + args,
        "create the next page.",
        mono=mono,
    )
