#! /usr/bin/env bash

function bluer_journal_open() {
    local options=$1

    local page=$(bluer_ai_option "$options" page latest)
    [[ "$page" == "latest" ]] &&
        page=$(python3 -m bluer_journal.utils get --what latest)

    local where=$(bluer_ai_option_choice "$options" code,web code)

    if [[ "$where" == "web" ]]; then
        local url="https://github.com/kamangir/$BLUER_JOURNAL_REPO/wiki"
        url="$url/$page"

        bluer_ai_browse $url
    elif [[ "$where" == "code" ]]; then
        local filename=$abcli_path_git/$BLUER_JOURNAL_REPO.wiki
        [[ "$page" != "home" ]] &&
            filename=$filename/$page.md

        bluer_ai_code $filename
    else
        bluer_ai_log_error "where=$where not found."
        return 1
    fi
}
