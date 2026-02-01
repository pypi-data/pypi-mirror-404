#! /usr/bin/env bash

function test_bluer_algo_socket() {
    local options=$1

    local object_name=test_bluer_algo_socket-$(bluer_ai_string_timestamp)
    local object_path=$ABCLI_OBJECT_ROOT/$object_name
    mkdir -pv $object_path
    pushd $object_path >/dev/null

    # Start receiver in background
    bluer_algo_socket test - \
        --what receiving >$object_path/received.txt &

    sleep 1 # wait for receiver to bind

    # Send message
    bluer_algo_socket test - \
        --what sending \
        --host $(hostname)

    sleep 1 # give receiver time to receive

    local output
    if grep -q hello-world received.txt; then
        output=0
        rm -v received.txt
    else
        echo "❌ Test failed"
        cat received.txt
        output=1
    fi

    popd >/dev/null

    return $output
}
