#!/bin/bash
# Recover UID and GID from ldaps://ldap.epfl.ch

ENABLE_WANDB=false
LDAP_USERNAME=""

if [[ "$1" = "-h" || "$1" = "--help" ]]; then
    echo "NAME
    ldap_fetch.sh Fetch credentials from ldaps://ldap.epfl.ch for GASPAR user

SYNOPSIS
    ./ldap_fetch.sh GASPAR
    ./ldap_fetch.sh GASPAR --wandb
"
    exit 0
fi

if [ $# -eq 1 ]; then
    LDAP_USERNAME="$1"
elif [ $# -eq 2 ] && [[ "$2" = "--wandb" ]]; then
    ENABLE_WANDB=true
    LDAP_USERNAME="$1"
else
    echo "Usage: ./ldap_fetch.sh GASPAR [--wandb]"
    exit 1
fi

if [[ -f ~/.profile ]] && grep "EPFL_USER" ~/.profile -q; then
    echo "Credentials already in ~/.profile file"
else

    # Require gaspar username
    if [ -z "$LDAP_USERNAME" ]; then
        echo "GASPAR username required"
        exit 1
    fi

    ldap_return=$( ldapsearch -x -b o=epfl,c=ch -H ldaps://ldap.epfl.ch \
        -LLL "(&(objectclass=person)(uid=$LDAP_USERNAME))" uid uidNumber gidNumber )


    LDAP_UID=$( perl -ne 'print /uidNumber: (.*)/' <<< "$ldap_return" )
    LDAP_GID=$( perl -ne 'print /gidNumber: (.*)/' <<< "$ldap_return" )
    if grep "ou=lts4" -q <<< "$ldap_return"
    then
        EPFL_SCRATCH_HOME='/mnt/lts4/scratch/home/$EPFL_USER'
    else
        EPFL_SCRATCH_HOME='/mnt/lts4/scratch/students/$EPFL_USER'
    fi

    echo "# Added by ldap_fetch.sh
export EPFL_USER=$LDAP_USERNAME
export EPFL_UID=$LDAP_UID
export EPFL_GROUPNAME=lts4
export EPFL_GID=$LDAP_GID
export EPFL_SUPPLEMENTAL_GROUPS=78680
export EPFL_SCRATCH_HOME=$EPFL_SCRATCH_HOME
" >> ~/.profile

    echo "Credentials stored in ~/.profile"
fi

if grep "RUNAI_OPTIONS" ~/.profile -q; then
    if $ENABLE_WANDB && ! grep "RUNAI_OPTIONS+=( --environment WANDB_API_KEY=SECRET:wandb-secret,secret )" ~/.profile -q; then
        echo "RUNAI_OPTIONS+=( --environment WANDB_API_KEY=SECRET:wandb-secret,secret )" >> ~/.profile
    fi
else
    echo 'export RUNAI_OPTIONS=(
    --run-as-uid $EPFL_UID
    --run-as-gid $EPFL_GID
    --supplemental-groups $EPFL_SUPPLEMENTAL_GROUPS
    --existing-pvc claimname=lts4-scratch,path=/mnt/lts4/scratch
    --environment HOME=/home/$EPFL_USER
    --environment SCRATCH_HOME=$EPFL_SCRATCH_HOME
)' >> ~/.profile

    if $ENABLE_WANDB; then
        echo "RUNAI_OPTIONS+=( --environment WANDB_API_KEY=SECRET:wandb-secret,secret )" >> ~/.profile
    fi
fi

if $ENABLE_WANDB && (! command -v kubectl >/dev/null 2>&1 || ! kubectl get secret wandb-secret >/dev/null 2>&1); then
    echo "Warning: '--wandb' was set but 'wandb-secret' is not available yet (or kubectl is not configured). Re-check requirements for how to set up wandb-secret."
fi

case $SHELL in
    "/bin/bash") dotfile="$HOME/.bashrc" ;;
    "/bin/zsh") dotfile="$HOME/.zshrc" ;;
    *)
        echo "Manually add profile loading to your shell rc"
        exit 0
        ;;
esac

if ! grep "source ~/.profile" $dotfile -q; then
    echo "source ~/.profile" >> $dotfile
    echo "Profile added to $dotfile"
fi
