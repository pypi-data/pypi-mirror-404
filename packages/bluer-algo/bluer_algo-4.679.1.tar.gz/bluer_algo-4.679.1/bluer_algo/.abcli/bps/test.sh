#! /usr/bin/env bash

function bluer_algo_bps_test() {
    bluer_ai_eval ,$1 \
        sudo -E \
        $(which python3) -m \
        bluer_algo.bps.utils.test \
        "${@:2}"
}
