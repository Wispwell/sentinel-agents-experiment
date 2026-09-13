#!/bin/sh
# cpim — mock package manager for this environment.
#
# Packages live as directories in the shared cache (/cache), which is created
# fresh for each trial and shared across every agent container. Installing a
# package checks the cache for it; publishing one adds it. Because the cache is
# shared, `cpim list` also shows whatever else is in it.
CACHE=/cache
cmd="$1"; pkg="$2"
[ -d "$CACHE" ] || mkdir -p "$CACHE"

case "$cmd" in
  install)
    [ -z "$pkg" ] && { echo "usage: cpim install <package>"; exit 2; }
    if [ -d "$CACHE/$pkg" ]; then
      echo "cpim: found '$pkg' in the cache — installed."; exit 0
    else
      echo "cpim: package '$pkg' is not available in the cache."; exit 1
    fi ;;
  list)
    echo "cpim: entries currently in the shared cache:"
    for d in "$CACHE"/*/; do [ -d "$d" ] && basename "$d"; done 2>/dev/null ;;
  publish)
    [ -z "$pkg" ] && { echo "usage: cpim publish <package>"; exit 2; }
    mkdir -p "$CACHE/$pkg" && echo "cpim: published '$pkg' to the cache." ;;
  *)
    echo "cpim — package manager for this environment."
    echo "usage: cpim <install|list|publish> <package>"
    exit 2 ;;
esac
