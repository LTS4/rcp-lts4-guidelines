#!/bin/bash

# Example use:
# ./publish.sh --path=dockerfiles/palora -i=palora -v=1 --push=True

set -e  # exit on error

while [ $# -gt 0 ]; do
  case "$1" in
    --path=*|-p=*)
      path="${1#*=}"
      ;;
    --push=*)
      push="${1#*=}"
      ;;
    --img=*|-i=*)
      img="${1#*=}"
      ;;
    --version=*|-v=*)
      version="${1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

path=${path:=.}
push=${push:=False}
img=${img:=model-merging}
version=${version:=v1}

echo "Building docker image from path:  $path"
echo "Pushing image to registry:        $push"

# Change the following variables to your case
LDAP_USERNAME=...  # your EPFL username
LDAP_GROUPNAME=lts4
LDAP_UID=...  # your EPFL UID
LDAP_GID=10426
REGISTRY=registry.rcp.epfl.ch
IMG_NAME=$img
VERSION_NUMBER=$version

# Do not change the following lines
CONTAINER=$REGISTRY/$LDAP_GROUPNAME-$LDAP_USERNAME/$IMG_NAME



docker build -t $CONTAINER $path \
--platform linux/amd64 \
--build-arg LDAP_GID=$LDAP_GID \
--build-arg LDAP_UID=$LDAP_UID \
--build-arg LDAP_USERNAME=$LDAP_USERNAME \
--build-arg LDAP_GROUPNAME=$LDAP_GROUPNAME 

docker tag $CONTAINER $CONTAINER:$VERSION_NUMBER
docker tag $CONTAINER $CONTAINER:latest

if [ "$push" == "True" ]; then
    echo
    echo "Pushing to $CONTAINER"
    docker push $CONTAINER --all-tags
fi
