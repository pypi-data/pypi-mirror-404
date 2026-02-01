#! /usr/bin/env bash

function test_bluer_algo_README() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_algo build_README
}
