#! /usr/bin/env bash

function bluer_algo_action_git_before_push() {
    bluer_algo build_README
    [[ $? -ne 0 ]] && return 1

    [[ "$(bluer_ai_git get_branch)" != "main" ]] &&
        return 0

    bluer_algo pypi build
}
