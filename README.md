# Getting started with RCP (LTS4)

This repository helps LTS4 members submit jobs to the [RCP CaaS cluster](https://wiki.rcp.epfl.ch/en/home/CaaS).

The RCP Wiki gives you a [Quick start guide](https://wiki.rcp.epfl.ch/home/CaaS/Quick_Start), which you can follow. However, we provide a base image which includes pixi and conda, which should cover a lot of use cases and means that you do not necessarily have to build your own image. The setup guide does not cover building your own image and defers to the RCP wiki. 

> [!IMPORTANT]
> **Network requirement**: You must be on the EPFL WiFi or connected to the VPN.

> [!IMPORTANT]
> Using the cluster creates costs. Please be mindful of the resources you use. **Do not forget to stop your jobs when not used!**

Content overview:
- [Setup Guide](#setup-guide)
  - [1. Setup Tools on Your Machine](#1-setup-tools-on-your-machine)
  - [2. Login to the Cluster](#2-login-to-the-cluster)
  - [3. Credentials](#3-ldap-credentials)
  - [4. (Optional) Weights and biases, HuggingFace, Claude and Codex](#4-optional-weights-and-biases-huggingface-claude-and-codex)
  - [5. (Optional) Symlinks](#5-optional-symlinks)
- [Launching jobs](#launching-jobs)
- [Using VS Code](#using-vs-code)

## Setup Guide

#### 1. Setup Tools on Your Machine

#### Install kubectl

Download and install kubectl v1.30.11 (matching the cluster version):

```bash
# macOS with Apple Silicon
curl -LO "https://dl.k8s.io/release/v1.30.11/bin/darwin/arm64/kubectl"

# Linux (AMD64)
# curl -LO "https://dl.k8s.io/release/v1.30.11/bin/linux/amd64/kubectl"

# Install
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
sudo chown root: /usr/local/bin/kubectl
``` 

See https://kubernetes.io/docs/tasks/tools/install-kubectl/ for other platforms.

#### Setup kubeconfig

Download the kube config file to `~/.kube/config`:

```bash
curl https://wiki.rcp.epfl.ch/public/files/kube-config.yaml -o ~/.kube/config && chmod 600 ~/.kube/config
```

#### Install run:ai CLI

Download and install the run:ai CLI:

```bash
# macOS with Apple Silicon
wget --content-disposition https://rcp-caas-prod.rcp.epfl.ch/cli/darwin

# Linux (replace 'darwin' with 'linux')
# wget --content-disposition https://rcp-caas-prod.rcp.epfl.ch/cli/linux

# Install
chmod +x ./runai
sudo mv ./runai /usr/local/bin/runai
sudo chown root: /usr/local/bin/runai
```

### 2. Login to the Cluster

#### Login to run:ai

```bash
runai login
```

#### Verify access

```bash
# List available projects
runai list projects

# Set your default project
runai config project lts4-$GASPAR_USERNAME
```

#### Verify Kubernetes connection

```bash
kubectl get nodes
```

You should see the RCP cluster nodes listed.

### 3. LDAP credentials

```bash
./ldap_fetch.sh GASPAR
```

This writes **`~/.profile`** only (`EPFL_*` and `RUNAI_OPTIONS` for `publish.sh`, and `csub.py`).


### 4. (Optional) Weights and biases, HuggingFace, Claude and Codex

For WandB, HF, Claude and Codex in containers, we need to transmit your API keys for these services. You can add these api keys as kubernetes secrets, and csub.py will check if they exist and add them to your job submissions. csub.py recognizes `hf-secret`, `wandb-secret`, `claude-secret` and `codex-secret`.

```
kubectl create secret generic hf-secret --from-literal=secret=$HF_TOKEN
kubectl create secret generic wandb-secret --from-literal=secret=$WANDB_TOKEN
```

### 5. (Optional) Symlinks

You have permanent storage on scratch at /mnt/lts4/scratch/home/$USERNAME. You may want the ephemeral "home" directory on your container to point to some files or directories there, such as your .zshrc.

For this, you can use `symlinks.json`, which is read by csub.py to create symbolic links between scratch and the home directory of your container. You can add a symlink by adding:
```
name_of_file_on_scratch: [file, name_of_symlink_in_container]
OR
name_of_dir_on_scratch: [dir, name_of_symlink_in_container]
```

Most of the time, the default symlinks.json will work just fine.

## Launching jobs

`csub.py` generates a Run:AI workload YAML and applies it with `kubectl`. You must pass an image (`-i` full URL or `-si` short name under your Harbor project).

**Interactive job** (default: sleeps for `--time`, default `12h`):

```bash
python csub.py -n my-interactive -si my-image -g 1 --node_type default
# Or full image URL:
python csub.py -n my-interactive -i registry.rcp.epfl.ch/lts4-$EPFL_USER/my-image:latest -g 0.8
```

Connect to the pod:

```bash
runai exec my-interactive -it -- zsh
```

**Training job**:

```bash
python csub.py -n train-job --train -si my-image -g 1 \
  --command="cd \$SCRATCH_HOME/myproject && python train.py --epochs 10"
```

**Dry-run** (print YAML only):

```bash
python csub.py -n test --dry -si my-image -g 0
```

Useful flags: `--cpus`, `--memory` (e.g. `32G`), `--node_type` (`h100`, `a100-40g`, `default`, …), `--large_shm` / `--no-large_shm`, `--host_ipc`, `--no_symlinks`, `--backofflimit` (train retries).

See also [useful_commands.md](useful_commands.md) and [useful_alias.md](useful_alias.md) for day-to-day Run:AI commands and shell shortcuts.


**Non-permanent LTS4 members** (students): check scratch path:

```bash
echo $EPFL_SCRATCH_HOME
# Expected: /mnt/lts4/scratch/students/<gaspar>
```

### Job management

```bash
runai list jobs
runai describe job <name>
runai logs <name>
runai logs <name> --pod <name>-0-<n>   # specific retry pod
runai delete job <name>
```

## Credits

This guide builds upon https://github.com/epfml/getting-started.
