#! /usr/bin/env bash

function test_bluer_journal_git_pull() {
    if [[ "$BLUER_AI_WEB_IS_ACCESSIBLE" == 0 ]]; then
        bluer_ai_log_warning "web is not accessible, test is disabled."
        return
    fi

    local options=$1

    bluer_journal_git_pull
}
