"""Shared network identity for the network-recon builtins.

Single source of truth for the emulated NIC's IP, MAC, gateway and netmask, so
``ifconfig`` and ``ip`` can never drift apart (a mismatched MAC across two
commands is an obvious tell). Underscore-prefixed so the registry's
``discover()`` imports it harmlessly — it registers no command.

MAC choice: the previous ``52:54:00`` prefix is QEMU/KVM's registered OUI and
flags the box as a virtual machine to anyone who checks. We use a Dell OUI
(``00:1a:a0``) instead — a commodity bare-metal server vendor — which matches
the on-disk DB-host persona better than announcing "I'm a VM". The IP stays on
the private /24 the rest of the fixtures assume.
"""

from __future__ import annotations

__all__ = ["ETH_IP", "ETH_MAC", "ETH_NETMASK", "ETH_BROADCAST", "GATEWAY"]

ETH_IP = "10.0.0.24"
ETH_MAC = "00:1a:a0:3f:7c:12"   # Dell OUI — bare-metal, not KVM's 52:54:00
ETH_NETMASK = "255.255.255.0"
ETH_BROADCAST = "10.0.0.255"
GATEWAY = "10.0.0.1"
