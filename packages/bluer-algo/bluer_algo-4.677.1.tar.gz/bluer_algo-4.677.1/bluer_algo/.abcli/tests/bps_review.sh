#! /usr/bin/env bash

function test_bluer_algo_bps_review() {
    local options=$1

    bluer_ai_eval ,$options \
        bluer_algo_bps review - \
        $BLUER_ALGO_BPS_REVIEW_TEST_OBJECT
}
