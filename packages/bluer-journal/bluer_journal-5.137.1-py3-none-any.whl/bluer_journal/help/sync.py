from typing import List

from bluer_options.terminal import show_usage, xtra
from bluer_options.env import BLUER_AI_WEB_IS_ACCESSIBLE

from bluer_journal import ALIAS
from bluer_journal.help.git import help_functions as help_git
from bluer_journal.help.git import pull_options, push_options

args = [
    "[--checklist 0]",
    "[--relations 0]",
    "[--verbose 1]",
]


def help_sync(
    tokens: List[str],
    mono: bool,
) -> str:
    options = xtra(
        "dryrun,{}".format("offline" if BLUER_AI_WEB_IS_ACCESSIBLE else "~offline"),
        mono=mono,
    )

    return show_usage(
        [
            "@journal",
            "sync",
            f"[{options}]",
            "[{}]".format(pull_options(mono=mono)),
            "[{}]".format(push_options(mono=mono, cascade=True)),
        ]
        + args,
        "sync journal.",
        mono=mono,
    )
