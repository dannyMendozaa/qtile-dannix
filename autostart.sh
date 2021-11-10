#!/usr/bin/env bash

#setxkbmap latam
numlockx on # Enabale numeric keyboard
blueman-applet & # Blueman APP
/usr/lib/bluetooth/obexd -n & # Sending/Receiving Files From Host/ExternalDevice
picom -b # Start the compositor - Add transparency to certain windows
