#! /usr/bin/env bash

function bluer_algo_bps_set_anchor() {
    local anchor=$1

    [[ "$anchor" == clear ]] &&
        anchor=""

    if [[ ! -z "$anchor" ]]; then
        python3 -m \
            bluer_algo.bps.utils.generate \
            --only_validate 1 \
            --as_str $anchor
        [[ $? -ne 0 ]] && return 1
    fi

    pushd $abcli_path_git/bluer-sbc >/dev/null

    dotenv set \
        BLUER_SBC_BPS_ANCHORED_AT \
        $anchor
    [[ $? -ne 0 ]] && return 1

    popd >/dev/null

    bluer_sbc init
}
