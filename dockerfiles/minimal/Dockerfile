# Base image
FROM python:3.13-slim

# Maintainer
LABEL maintainer="William Cappelletti <william.cappelletti@epfl.ch>"

# Create your user in the container
ARG LDAP_USERNAME
ARG LDAP_UID
ARG LDAP_GROUPNAME
ARG LDAP_GID

RUN groupadd ${LDAP_GROUPNAME} --gid ${LDAP_GID}
RUN useradd -m -s /bin/bash -g ${LDAP_GROUPNAME} -u ${LDAP_UID} ${LDAP_USERNAME}

# Copy your code in the container
# COPY workdir/ /home/${LDAP_USERNAME}

# # Install required packages
RUN apt update
RUN apt install git -y
# RUN apt install python3-pip -y

ENV HOME=/home/${LDAP_USERNAME}
RUN mkdir -p ${HOME}
# Set your user as owner of the new copied files
RUN chown -R ${LDAP_USERNAME}:${LDAP_GROUPNAME} ${HOME}


# Set the working directory in your user's home
WORKDIR ${HOME}
USER ${LDAP_USERNAME}

COPY requirements.txt ${HOME}/

# Install additional dependencies
RUN pip install -r requirements.txt
