FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Remove stale yarn apt source whose GPG key causes apt-get update to fail,
# which in turn breaks devcontainer feature installs (e.g. desktop-lite).
RUN rm -f /etc/apt/sources.list.d/yarn.list 2>/dev/null; exit 0
