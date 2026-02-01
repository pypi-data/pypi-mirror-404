import os
from typing import List, Tuple

from bluer_options import string
from bluer_objects import file
from bluer_objects.env import abcli_path_git

from bluer_journal import env
from bluer_journal.utils.latest import latest
from bluer_journal.logger import logger


def next(
    create: bool = True,
    verbose: bool = False,
) -> Tuple[bool, str]:
    suffix: int = 0
    while True:
        next_page: str = "dev-{}{}".format(
            string.pretty_date(
                as_filename=True,
                include_time=False,
                include_seconds=False,
            ),
            f"-{suffix:03d}" if suffix else "",
        )

        next_filename = os.path.join(
            abcli_path_git,
            f"{env.BLUER_JOURNAL_REPO}.wiki",
            f"{next_page}.md",
        )

        if not file.exists(next_filename):
            break

        suffix += 1

    if not create:
        return True, next_page

    # --

    success, latest_page = latest()
    if not success:
        return False, next_page

    logger.info(f"processing latest page: {latest_page}")
    latest_filename = os.path.join(
        abcli_path_git,
        f"{env.BLUER_JOURNAL_REPO}.wiki",
        f"{latest_page}.md",
    )

    success, page_content = file.load_text(
        latest_filename,
        log=verbose,
    )
    if not success:
        return False, next_page

    latest_page_content_updated: List[str] = []
    next_page_content: List[str] = [
        "---",
        "",
    ]
    fire_started: bool = False
    for line in page_content:
        if any(marker in line for marker in "🔥🎰"):
            fire_started = True

        if fire_started:
            next_page_content.append(line)
        else:
            latest_page_content_updated.append(line)

    latest_page_content_updated.append(f"--> [[{next_page}]]")

    if not file.save_text(
        latest_filename,
        latest_page_content_updated,
        log=verbose,
    ):
        return False, next_page

    # ---

    logger.info(f"processing next page: {next_page}")
    if not file.save_text(
        next_filename,
        next_page_content,
        log=verbose,
    ):
        return False, next_page

    # ---

    return True, next_page
