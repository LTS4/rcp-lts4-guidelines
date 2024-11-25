# Getting started with RCP

This guide builds upon https://github.com/epfml/getting-started.

## Requirements

[This guide](https://wiki.rcp.epfl.ch/home/CaaS/Quick_Start) is a good starting point for the requirements.

1. Install docker and sudoless docker. Follow this link: https://wiki.rcp.epfl.ch/en/home/CaaS/FAQ/how-to-build-a-container
2. Install kubernetes
   1. follow the instructions in the [wiki.rcp.epfl.ch](https://wiki.rcp.epfl.ch)
3. Install runai using the instructions in the wiki
   1. login to the RunAI platform using `runai login`. You should be able to run `runai whoami` afterwards
4. `registry.rcp.epfl.ch`
   1. go to registry.rcp.epfl.ch and login
   2. create your project with the UI. Your project should be `lts4-$USERNAME`
   3. login with docker to the registry by `docker login registry.rcp.epfl.ch`
5. Create a wandb secret and name it `wandb-secret`. This is needed for the wandb integration. Follow this link: https://wiki.rcp.epfl.ch/home/CaaS/FAQ/how-to-use-secret
6. For Visual Studio Code integration, follow this link: https://wiki.rcp.epfl.ch/en/home/CaaS/FAQ/how-to-vscode
7. `haas`
   1. Make sure you have access to the `haas` storage by running `ssh $USERNAME@haas001.rcp.epfl.ch`
   2. go to your mounted volume (should be `/mnt/lts4/scratch` for most) and create a directory with your name via `mkdir -p /mnt/lts4/scratch/home/$USERNAME`. The launch script assumes that you have done so.

Now you can proceed with the next steps, building your docker image, pushing it to the registry and launching jobs.

## Recover LDAP accreditation

First, you must recover and save your LDAP accreditation codes. You can use the `ldap_fetch.sh` script as follows, where `GASPAR` is your EPFL username:
```bash
./ldap_fetch.sh GASPAR
```

This will store your credentials in the `~/.profile` file, and make them available at startup by sourcing them it to your `.bashrc` or `.zshrc` files.

## Building your docker image

The base image uses a specific pytorch image for reproducibility, adds several libraries, adds the current user.

If you want to add more template images, create a directory in the `dockerfiles` directory and add a `Dockerfile` there.
Then, make a PR.

Then, run the following line to push your image to the registry (if you only want to build the image without pushing it to the registry, omit the `push`).

```bash
# Before running this command, make sure to change $GASPAR to your epfl username, or declare it as
# an environment variable
./publish.sh --path=dockerfiles/base \
   --user=$GASPAR
   --img=NAME_OF_YOUR_IMAGE \
   --version=1 \
   --push=True
```


## Launching a job

More detailed information coming soon, take a look at the `launch.py` script for now.

### (Optional) Make the launch script available in your path
To use the launch script from anywhere, you can add an alias to your `.bashrc` or `.zshrc` file.
```bash
# Add the following line to your .bashrc or .zshrc
# ...for bash
echo 'alias rcplaunch="python /path/to/launch.py"' >> ~/.bashrc
source ~/.bashrc

# ...for zsh
echo 'alias rcplaunch="python /path/to/launch.py"' >> ~/.zshrc
source ~/.zshrc
```


### Interactive job
```bash
# You can specify a fraction of the GPU to use with the `--gpus` flag
python launch.py \
    --name=NAME_OF_JOB \
    --gpus=0.8 \
    --image=CONTAINER_NAME:VERSION \
    --interactive
```

### Training job
```bash
python launch.py \
    --name=NAME_OF_JOB \
    --shm=10 \
    --gpus=1 \
    --cpus=20 \
    --image=CONTAINER_NAME:VERSION \
    --command='cd path/to/code && python train.py --arg1=1 --arg2=2'
```

### Do not launch but only print out the yaml config file
```bash
python launch.py \
    --name=NAME_OF_JOB \
    --shm=10 \
    --gpus=1 \
    --cpus=20 \
    --image=CONTAINER_NAME:VERSION \
    --command='cd path/to/code && python train.py --arg1=1 --arg2=2' \
    --dry-run
```