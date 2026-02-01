#! /usr/bin/env bash

function bluer_journal_next() {
    local page=$(python3 -m bluer_journal.utils get \
        --what next \
        --create 1 \
        "${@:4}")
    page=$(bluer_ai_clarify_input $1 $page)

    local options=$2
    local do_open=$(bluer_ai_option_int "$options" open 1)
    [[ "$do_open" == 1 ]] &&
        bluer_journal_open code,page=$page

    local push_options=$3
    local do_push=$(bluer_ai_option_int "$push_options" push 1)
    if [[ "$do_push" == 1 ]]; then
        bluer_journal_git_push ~sync,$push_options
    fi
}
