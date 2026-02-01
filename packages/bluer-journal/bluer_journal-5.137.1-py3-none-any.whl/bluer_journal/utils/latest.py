import os
from typing import Tuple

from bluer_objects import file
from bluer_objects.env import abcli_path_git
from bluer_journal import env


def latest() -> Tuple[bool, str]:
    list_of_files = sorted(
        [
            filename
            for filename in [
                file.name(filename)
                for filename in file.list_of(
                    os.path.join(
                        abcli_path_git,
                        f"{env.BLUER_JOURNAL_REPO}.wiki",
                        "*.md",
                    )
                )
            ]
            if filename.startswith("dev-")
        ]
    )

    if list_of_files:
        return True, list_of_files[-1]

    return False, ""
