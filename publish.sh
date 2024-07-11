#!/bin/bash

set -e  # exit on error

REGISTRY=registry.rcp.epfl.ch
LDAP_GROUPNAME=lts4
LDAP_USERNAME=...
IMG_NAME=base
VERSION=v1

CONTAINER=$REGISTRY/$LDAP_GROUPNAME-$LDAP_USERNAME/$IMG_NAME

docker build -t $CONTAINER .

docker tag $CONTAINER $CONTAINER:$VERSION
docker tag $CONTAINER $CONTAINER:latest

if [ "$1" == "push" ]; then
    echo
    echo "Pushing to $CONTAINER"
    docker push $CONTAINER --all-tags
fi


