# Direct-mode container (optional). Default demo runs the simulator on the host.
#
# This image MUST NOT be used with BIND_MODE=5g: Docker bridge networking cannot
# bind UERANSIM uesimtunN interfaces, and this repo never uses network_mode: host.
