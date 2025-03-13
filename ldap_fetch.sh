#!/bin/bash
# Recover UID and GID from ldaps://ldap.epfl.ch

if [[ $1 = "-h" || $1 = "--help" ]]; then
    echo "NAME
    ldap_fetch.sh Fetch credentials from ldaps://ldap.epfl.ch for GASPAR user

SYNOPSIS
    ./ldap_fetch.sh GASPAR
"
    exit 0
fi

if [[ -f ~/.profile ]] && grep "EPFL_USER" ~/.profile -q; then
    echo "Credentials already in ~/.profile file"
else

    # Require gaspar username
    if [ -z "$1" ]; then
        echo "GASPAR username required"
        exit 1
    fi

    LDAP_USERNAME="$1"

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

grep "RUNAI_OPTIONS" ~/.profile -q || echo 'export RUNAI_OPTIONS=(
    --run-as-uid $EPFL_UID
    --run-as-gid $EPFL_GID
    --supplemental-groups $EPFL_SUPPLEMENTAL_GROUPS
    --existing-pvc claimname=lts4-scratch,path=/mnt/lts4/scratch
    --environment HOME=/home/$EPFL_USER
    --environment SCRATCH_HOME=$EPFL_SCRATCH_HOME
)' >> ~/.profile

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