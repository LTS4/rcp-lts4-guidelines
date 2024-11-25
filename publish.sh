#!/bin/bash

# Example use:
# ./publish.sh --user=gaspar --path=dockerfiles/palora -i=palora -v=1 --push=True

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
IMG_NAME=${img:=container}
version=${version:=v1}

echo "Building docker image from path:  $path"
echo "Pushing image to registry:        $push"

REGISTRY=registry.rcp.epfl.ch
VERSION_NUMBER=$version

# Do not change the following lines
CONTAINER=$REGISTRY/$EPFL_GROUPNAME-$EPFL_USER/$IMG_NAME

docker build -t $CONTAINER $path \
--platform linux/amd64 \
--build-arg LDAP_GID=$EPFL_GID \
--build-arg LDAP_UID=$EPFL_UID \
--build-arg LDAP_USERNAME=$EPFL_USER \
--build-arg LDAP_GROUPNAME=$EPFL_GROUPNAME

docker tag $CONTAINER $CONTAINER:$VERSION_NUMBER
docker tag $CONTAINER $CONTAINER:latest

if [ "$push" == "True" ]; then
    echo
    echo "Pushing to $CONTAINER"
    docker push $CONTAINER --all-tags
fi
