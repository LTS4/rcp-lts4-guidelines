# Base PyTorch Image with LaTeX support and VScode extensions preinstalled.
# Modify the requirements.txt file to install the necessary python packages for your project.
# The image will not have conda. If you wish to install additional packages in interactive jobs, you can do so with pip.

# Base image
FROM nvcr.io/nvidia/pytorch:24.01-py3

# Maintainer
LABEL maintainer="Nikolaos Dimitriadis <dimitriadisnikolaos0@gmail.com>"

# Build arguments (change them to your case)
ARG LDAP_USERNAME=ndimitri
ARG LDAP_GROUPNAME=lts4
ARG LDAP_UID=229754
ARG LDAP_GID=10426

ENV LDAP_USERNAME=${LDAP_USERNAME}
ENV LDAP_GROUPNAME=${LDAP_GROUPNAME}
ENV LDAP_UID=${LDAP_UID}
ENV LDAP_GID=${LDAP_GID}

ENV DEBIAN_FRONTEND=noninteractive

# Do all tasks to be done with root privileged
RUN echo "Etc/UTC" > /etc/timezone && \
    ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    apt-get update && apt-get install -y --no-install-recommends \
        # sudo \
        build-essential \
        ca-certificates \
        pkg-config \
        tzdata \
        inkscape \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-fonts-extra \
        texlive-latex-recommended \
        texlive-xetex \
        dvipng \
        cm-super \
        jed \
        libsm6 \
        libxext-dev \
        libxrender1 \
        lmodern \
        libcurl3-dev \
        libfreetype6-dev \
        libzmq3-dev \
        libcupti-dev \
        pkg-config \
        libjpeg-dev \
        libpng-dev \
        zlib1g-dev \
        locales \
        rsync \
        cmake \
        g++ \
        swig \
        vim \
        git \
        curl \
        wget \
        unzip \
        zsh \
        git \
        nodejs \
        npm \
        gpg \
        screen \
        tmux \
        openssh-server \
        fish \
        htop \
     && rm -rf /var/lib/apt/lists/*


RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# RUN mkdir -p /home/${LDAP_USERNAME}/.config/

# Create local user and group
RUN groupadd ${LDAP_GROUPNAME} -g ${LDAP_GID} && \
    useradd -m -s /bin/bash -N -u ${LDAP_UID} -g ${LDAP_GID} ${LDAP_USERNAME} && \
    echo "${LDAP_USERNAME}:${LDAP_USERNAME}" | chpasswd && \
    usermod -aG sudo,adm,root ${LDAP_USERNAME} && \
    chown -R ${LDAP_USERNAME}:${LDAP_GROUPNAME} ${HOME} && \
    echo "${LDAP_USERNAME}   ALL = NOPASSWD: ALL" > /etc/sudoers


# install rust and pueue
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN echo 'source $HOME/.cargo/env' >> $HOME/.bashrc 
RUN cargo install pueue --locked 


# install everything else with pip
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install gpustat black jupyter jupyterlab notebook nvitop nvidia-ml-py
RUN pip install --ignore-installed --no-cache-dir -r requirements.txt

RUN mkdir -p /docker/
COPY .aliases /docker/
COPY entrypoint.sh /docker/
RUN chmod +x /docker/entrypoint.sh

# Install Visual Studio Code Server
RUN curl -fsSL https://code-server.dev/install.sh | sh

RUN mkdir -p /home/${LDAP_USERNAME}/.vscode-server/extensions && \
    chmod -R 755 /home/${LDAP_USERNAME}/.vscode-server && \
    chown -R ${LDAP_USERNAME}:${LDAP_GROUPNAME} /home/${LDAP_USERNAME}/.vscode-server


## Switch to the local user
USER ${LDAP_USERNAME}

RUN code-server --install-extension ms-python.python --extensions-dir /home/${LDAP_USERNAME}/.vscode-server/extensions/ \
 && code-server --install-extension ms-python.black-formatter --extensions-dir /home/${LDAP_USERNAME}/.vscode-server/extensions/ \
 && code-server --install-extension gruntfuggly.todo-tree --extensions-dir /home/${LDAP_USERNAME}/.vscode-server/extensions/ \
 && code-server --install-extension ms-python.debugpy --extensions-dir /home/${LDAP_USERNAME}/.vscode-server/extensions/ \
 && code-server --install-extension ms-toolsai.jupyter --extensions-dir /home/${LDAP_USERNAME}/.vscode-server/extensions/

WORKDIR /home/${LDAP_USERNAME}

ENTRYPOINT [ "/docker/entrypoint.sh" ]
CMD ["fish"]