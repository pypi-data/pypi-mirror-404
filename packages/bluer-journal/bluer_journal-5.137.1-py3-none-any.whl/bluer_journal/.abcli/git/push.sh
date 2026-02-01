#! /usr/bin/env bash

function bluer_journal_git_push() {
    local options=$1
    local do_dryrun=$(bluer_ai_option_int "$options" dryrun 0)
    local do_offline=$(bluer_ai_not $BLUER_AI_WEB_IS_ACCESSIBLE)
    do_offline=$(bluer_ai_option_int "$options" offline $do_offline)
    local do_push=$(bluer_ai_option_int "$options" push 1)
    local do_sync=$(bluer_ai_option_int "$options" sync 1)
    local is_token=$(bluer_ai_option_int "$options" token 0)

    if [[ "$do_sync" == 1 ]]; then
        bluer_journal_sync \
            dryrun=$do_dryrun - \
            ~push,offline=$do_offline
        [[ $? -ne 0 ]] && return 1
    fi

    if [[ "$do_push" == 1 ]]; then
        local message="@journal git push"

        if [[ "$is_token" == 1 ]]; then
            pushd $abcli_path_git/$BLUER_JOURNAL_REPO.wiki >/dev/null
            [[ $? -ne 0 ]] && return 1

            git add .
            git commit -a -m "$message"

            bluer_ai_eval dryrun=$do_dryrun \
                git push "https://$BLUER_AI_GITHUB_TOKEN@github.com/kamangir/$BLUER_JOURNAL_REPO.wiki.git"
            [[ $? -ne 0 ]] && return 1

            popd >/dev/null
        else
            bluer_ai_git \
                $BLUER_JOURNAL_REPO.wiki \
                push \
                "$message" \
                ~increment_version,offline=$do_offline,~test
        fi
    fi
}
