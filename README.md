# BEL library and API

TODO:  https://github.com/gigamonkey/monorepoize

## Development Setup

### Requirements

1. git
1. python3.7
1. poetry


### Setup

1. git clone git@github.com:belbio/bel.git
1. cd bel/lib
1. poetry install
1. Add {.venv|venv}/lib/python3.7/site-packages/local.pth with rootdir of BEL library (e.g. /home/me/code/bel/bel) - the first 'bel' directory is the git repo root, the second is the bel or api directory level - the third 'bel' directory is the bel library code


## Notes

- Async wrapper for sync functions: https://dev.to/0xbf/turn-sync-function-to-async-python-tips-58nn
- https://hackernoon.com/controlling-python-async-creep-ec0a0f4b79ba
- https://github.com/w1z2g3/syncasync
