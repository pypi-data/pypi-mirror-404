#! /usr/bin/env bash

function bluer_algo_bps_install() {
    bluer_ai_log "installing bps ..."

    local asset_path=$(python3 -m bluer_algo locate)/assets/bps
    bluer_ai_log "asset path: $asset_path"

    sudo apt update
    sudo apt install -y \
        bluez \
        python3-dbus \
        python3-gi \
        libglib2.0-dev \
        libcairo2-dev \
        pkg-config \
        cmake

    pip3 install bluezero
    pip3 install dbus-next
    pip3 install bleak

    # bluez
    bluer_ai_log "installing bluez ..."

    sudo apt install --reinstall bluez -y

    # --experimental
    bluer_ai_log "turning experimental on ..."

    sudo mkdir -pv /etc/systemd/system/bluetooth.service.d

    sudo cp -v \
        $asset_path/override.conf \
        /etc/systemd/system/bluetooth.service.d/override.conf

    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload

    sudo systemctl restart bluetooth

    ps -eo args | grep [b]luetoothd

    sudo install -m 644 \
        $asset_path/org.example.Hello.conf \
        /etc/dbus-1/system.d/org.example.Hello.conf
}
