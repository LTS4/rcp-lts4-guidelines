#!/bin/bash
set -e
pueued -d

source /docker/.aliases
exec "$@"