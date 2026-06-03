#!/bin/bash
set -e
set -x

echo "NB_USER=$NB_USER NB_UID=$NB_UID WORKING_DIR=$WORKING_DIR"

if [[ -z $NB_USER ]] || [[ -z $NB_UID ]] || [[ -z $NB_GROUP ]] || [[ -z $NB_GID ]] || [[ -z $WORKING_DIR ]]; then
  exec "$@"
  exit
fi

su - root <<! >/dev/null 2>&1
root
groupadd $NB_GROUP -g $NB_GID
useradd -M -s /bin/bash -N -u $NB_UID -g $NB_GID $NB_USER
echo "${NB_USER}:${NB_USER}" | chpasswd
usermod -aG sudo,adm,root ${NB_USER}
mkdir -p /home/${NB_USER}
chown ${NB_USER}:$NB_GROUP /home/${NB_USER}
echo "${NB_USER}   ALL=(ALL:ALL) ALL" >> /etc/sudoers
chsh -s /bin/zsh ${NB_USER}
rm -rf /home/${NB_USER}/.zshrc
!

mkdir -p ${WORKING_DIR}

if [[ -z $SYMLINK_TARGETS ]] || [[ -z $SYMLINK_PATHS ]] || [[ -z $SYMLINK_TYPES ]]; then
  exec "$@"
  exit
fi

echo "SYMLINK_TARGETS=$SYMLINK_TARGETS"
echo "SYMLINK_PATHS=$SYMLINK_PATHS"
echo "SYMLINK_TYPES=$SYMLINK_TYPES"
which pixi || true
pixi --version || true

IFS=: read -r -d '' -a target_array < <(printf '%s:\0' "$SYMLINK_TARGETS")
IFS=: read -r -d '' -a path_array < <(printf '%s:\0' "$SYMLINK_PATHS")
IFS=: read -r -d '' -a types_array < <(printf '%s:\0' "$SYMLINK_TYPES")
for index in ${!target_array[*]}; do
  if [[ -f ${path_array[$index]} ]] || [[ -d ${path_array[$index]} ]]; then
    echo "ERROR: path '${path_array[$index]}' already exists"
    exit 1
  fi

  if [[ -f ${target_array[$index]} ]] || [[ -d ${target_array[$index]} ]]; then
    ln -s ${target_array[$index]} ${path_array[$index]}
  else
    if [ ${types_array[$index]} == "conda" ]; then
      echo "Installing Miniconda to ${target_array[$index]}..."
      wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ${WORKING_DIR}/miniconda.sh
      /bin/bash ${WORKING_DIR}/miniconda.sh -b -p ${target_array[$index]}
      rm -rf ${WORKING_DIR}/miniconda.sh
      ${target_array[$index]}/bin/conda init zsh
      source ~/.zshrc
    else
      FILENAME="$(basename ${target_array[$index]})"
      if [[ -f /docker/${FILENAME} ]] || [[ -d /docker/${FILENAME} ]]; then
        cp -r /docker/${FILENAME} ${target_array[$index]}
        chown -R ${NB_USER}:$NB_GROUP ${target_array[$index]}
      elif [ ${types_array[$index]} == "dir" ]; then
        mkdir -p ${target_array[$index]}
      elif [ ${types_array[$index]} == "file" ]; then
        touch ${target_array[$index]}
      else
        echo "ERROR: SYMLINK_TYPES must be 'dir', 'file', or 'conda'"
        exit 1
      fi
    fi
    ln -s ${target_array[$index]} ${path_array[$index]}
  fi
done

cd ~
exec "$@"
