FROM pytorch/pytorch:2.3.1-cuda11.8-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive

# Do all tasks to be done with root privileged
RUN echo "Etc/UTC" > /etc/timezone && \
    ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        pkg-config \
        tzdata \
        inkscape \
        texlive-latex-base \
        dvipng \
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
     && rm -rf /var/lib/apt/lists/*


RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Build arguments
ARG LDAP_USERNAME=ndimitri
ARG LDAP_GROUPNAME=lts4
ARG LDAP_UID=229754
ARG LDAP_GID=10426

# Create local user and group
RUN groupadd $LDAP_GROUPNAME -g $LDAP_GID && \
    useradd -m -s /bin/bash -N -u $LDAP_UID -g $LDAP_GID $LDAP_USERNAME && \
    echo "${LDAP_USERNAME}:${LDAP_USERNAME}" | chpasswd && \
    usermod -aG sudo,adm,root ${LDAP_USERNAME} && \
    chown -R ${LDAP_USERNAME}:${LDAP_GROUPNAME} ${HOME} && \
    echo "${LDAP_USERNAME}   ALL = NOPASSWD: ALL" > /etc/sudoers



# Install Visual Studio Code Server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install VS Code and extensions
RUN code-server --install-extension ms-python.python 

RUN code --install-extension ms-python.black-formatter --no-sandbox --user-data-dir /usr/bin --force
RUN code --install-extension gruntfuggly.todo-tree --no-sandbox --user-data-dir /usr/bin --force

# install rust and pueue
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN cargo install pueue --locked 
RUN pueued -d

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install gpustat black 
RUN pip install -r requirements.txt

RUN mkdir -p /docker/
COPY .config/* /docker/
RUN chmod +x /docker/entrypoint.sh

## Switch to the local user
USER ${LDAP_USERNAME}
WORKDIR /home/${LDAP_USERNAME}

ENTRYPOINT [ "/docker/entrypoint.sh" ]
CMD ["fish"]