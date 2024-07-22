#!/bin/bash

set -e  # exit on error

# Change the following variables to your case
LDAP_USERNAME=...  # your EPFL username
LDAP_GROUPNAME=lts4
LDAP_UID=...  # your EPFL UID
LDAP_GID=10426
REGISTRY=registry.rcp.epfl.ch
IMG_NAME=base
VERSION=v1

# Do not change the following lines
CONTAINER=$REGISTRY/$LDAP_GROUPNAME-$LDAP_USERNAME/$IMG_NAME

docker build -t $CONTAINER . \
--build-arg LDAP_GID=$LDAP_GID \
--build-arg LDAP_UID=$LDAP_UID \
--build-arg LDAP_USERNAME=$USERNAME \
--build-arg LDAP_GROUPNAME=$LDAP_GROUPNAME

docker tag $CONTAINER $CONTAINER:$VERSION
docker tag $CONTAINER $CONTAINER:latest

if [ "$1" == "push" ]; then
    echo
    echo "Pushing to $CONTAINER"
    docker push $CONTAINER --all-tags
fi


