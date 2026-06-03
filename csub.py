#!/usr/bin/python3

import argparse
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pprint import pprint

from user_config import load_user_config

parser = argparse.ArgumentParser(description="Cluster Submit Utility")
parser.add_argument(
    "-n",
    "--name",
    type=str,
    required=False,
    help="Job name (has to be unique in the namespace)",
)
parser.add_argument(
    "-cl",
    "--cluster",
    type=str,
    default="rcp-caas",
    choices=["ic-caas", "rcp-caas"],
)
parser.add_argument(
    "-c",
    "--command",
    type=str,
    required=False,
    help="Command to run on the instance (default sleep for duration)",
)
parser.add_argument(
    "-t",
    "--time",
    default="12h",
    type=str,
    required=False,
    help="The maximum duration allowed for this job (default 6h)",
)
parser.add_argument(
    "-g",
    "--gpus",
    type=float,
    default=1,
    required=False,
    help="The number of GPUs requested (default 1)",
)
parser.add_argument(
    "--cpus",
    type=int,
    default=None,
    required=False,
    help="The number of CPUs requested",
)
parser.add_argument(
    "--memory",
    type=str,
    default="64G",
    required=False,
    help="The minimum amount of CPU memory (default 8G). must match regular expression '^([+-]?[0-9.]+)([eEinumkKMGTP]*[-+]?[0-9]*)$'",
)

select_image_group = parser.add_mutually_exclusive_group(required=True)
select_image_group.add_argument(
    "-si",
    "--short_image",
    type=str,
    help="The short name of the docker image that will be used for the job",
)
select_image_group.add_argument(
    "-i",
    "--image",
    type=str,
    help="The URL of the docker image that will be used for the job",
)

parser.add_argument(
    "-p",
    "--port",
    type=int,
    required=False,
    help="A cluster port for connect to this node",
)
parser.add_argument(
  "-u",
  "--local-config",
  type=str,
  default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "symlinks.json"),
  dest="local_config",
  help="Path to symlinks.json for symlinks; identity from ~/.profile",
)
parser.add_argument(
    "--train",
    action="store_true",
    help="train job (default is interactive, which has higher priority)",
)
parser.add_argument(
    "-d",
    "--dry",
    action="store_true",
    help="Print the generated yaml file instead of submitting it",
)
parser.add_argument(
    "--backofflimit",
    default=0,
    type=int,
    help="specifies the number of retries before marking a workload as failed (default 0). only exists for train jobs",
)
parser.add_argument(
    "--node_type",
    type=str,
    default="",
    choices=["", "g9", "g10", "v100", "a100", "a100-40g", "h100", "h200", "default"],
    help="node type to run on (default is empty, which means any node). \
          IC cluster: g9 for V100, g10 for A100. \
          RCP-Prod cluster: h100 for H100, use 'default' to get A100 on interactive jobs",
)
parser.add_argument(
    "--host_ipc",
    action="store_true",
    help="created workload will use the host's ipc namespace",
)
parser.add_argument(
    "--no_symlinks",
    action="store_true",
    help="do not create symlinks to the user's home directory",
)
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--large_shm",
    dest="large_shm",
    action="store_true",
    help="Use large shared memory /dev/shm for the job (default: True)",
)
group.add_argument(
    "--no-large_shm",
    dest="large_shm",
    action="store_false",
    help="Do not use large shared memory /dev/shm for the job",
)
parser.set_defaults(large_shm=True)


def _cluster_secret_exists(name: str) -> bool:
    try:
        result = subprocess.run(
            ["kubectl", "get", "secret", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    args = parser.parse_args()


    user_cfg = load_user_config(args.local_config)

    if args.short_image is not None:
        args.image = f"registry.rcp.epfl.ch/lts4-{user_cfg['user']}/{args.short_image}:latest"

    scratch_name = "lts4-scratch"  #  f"runai-mlo-{user_cfg['user']}-scratch"
    runai_cli_version = "2.22.73"

    if args.name is None:
        args.name = f"{user_cfg['user']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    if args.time is None:
        args.time = 7 * 24 * 60 * 60
    else:
        pattern = r"((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s?)?"
        match = re.match(pattern, args.time)
        parts = {k: int(v) for k, v in match.groupdict().items() if v}
        args.time = int(timedelta(**parts).total_seconds())

    if args.command is None:
        args.command = f"sleep {args.time}"

    if args.train:
        workload_kind = "TrainingWorkload"
    else:
        workload_kind = "InteractiveWorkload"

    working_dir = user_cfg["working_dir"]
    symlinks = user_cfg.get("symlinks") or {}
    if not args.no_symlinks and symlinks:
        symlink_targets, symlink_destinations = zip(*symlinks.items())
        symlink_targets = ":".join(
            [os.path.join(working_dir, target) for target in symlink_targets]
        )
        symlink_paths = ":".join(
            [
                os.path.join(f"/home/{user_cfg['user']}", dest[1])
                for dest in symlink_destinations
            ]
        )
        symlink_types = ":".join([dest[0] for dest in symlink_destinations])
    else:
        symlink_targets = ""
        symlink_paths = ""
        symlink_types = ""

    optional_env = ""
    if _cluster_secret_exists("wandb-secret"):
        optional_env += """
      WANDB_API_KEY:
        value: SECRET:wandb-secret,secret"""
    if _cluster_secret_exists("hf-secret"):
        optional_env += """
      HF_TOKEN:
        value: SECRET:hf-secret,secret"""

    cpu_section = ""
    if args.cpus is not None:
        cpu_section = f"""
  cpu:
    value: "{args.cpus}"
"""
    # this is the yaml file that will be submitted to the cluster
    cfg = f"""
apiVersion: run.ai/v2alpha1
kind: {workload_kind}
metadata:
  annotations:
    runai-cli-version: {runai_cli_version}
  labels:
    PreviousJob: "true"
  name: {args.name}
  
spec:
  name:
    value: {args.name}
  arguments: 
    value: "/bin/zsh -c 'source ~/.zshrc && {args.command}'" # zshrc is just loaded to have some env variables ready
  environment:
    items:
      HOME:
        value: "/home/{user_cfg['user']}"
      VIRTUAL_HOME:
        value: "/mnt/lts4/scratch/home/{user_cfg['user']}"
      NB_USER:
        value: {user_cfg['user']}
      NB_UID:
        value: "{user_cfg['uid']}"
      NB_GROUP:
        value: {user_cfg['group']}
      NB_GID:
        value: "{user_cfg['gid']}"
      WORKING_DIR:
        value: "{working_dir}"
      SYMLINK_TARGETS:
        value: "{symlink_targets}"
      SYMLINK_PATHS:
        value: "{symlink_paths}"
      SYMLINK_TYPES:
        value: "{symlink_types}"{optional_env}
      EPFML_LDAP:
        value: {user_cfg['user']}
  gpu:
    value: "{args.gpus}"
{cpu_section}
  memory:
    value: "{args.memory}"
  image:
    value: {args.image}
  imagePullPolicy:
    value: Always
  pvcs:
    items:
      pvc--0:
        value:
          claimName: {scratch_name}
          existingPvc: true
          path: /mnt/lts4/scratch
          readOnly: false
  ## these two lines are necessary on RCP, not on the new IC
  runAsGid:
    value: {user_cfg['gid']}
  runAsUid:
    value: {user_cfg['uid']}
  ##
  runAsUser: 
    value: true    
  serviceType:
    value: ClusterIP
  username:
    value: {user_cfg['user']}
  allowPrivilegeEscalation:  # allow sudo
    value: true
  supplementalGroups:
    value: "{user_cfg['supplemental_groups']}"
"""

    #### some additional flags that can be added at the end of the config
    if args.node_type in [
        "g9",
        "g10",
        "v100",
        "a100",
        "a100-40g",
        "h100",
        "h200",
        "default",
    ]:
        cfg += f"""
  nodePools:
    value: {args.node_type} # g10 for A100, g9 for V100 (only on IC cluster)
"""
    if args.host_ipc:
        cfg += f"""
  hostIpc:
    value: true
"""

    if args.train:
        cfg += f"""
  backoffLimit: 
    value: {args.backofflimit}
"""
    if args.large_shm:
        cfg += f"""
  largeShm:
    value: true
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
        f.write(cfg)
        f.flush()
        if args.dry:
            print(cfg)
        else:
            # Run the subprocess and capture stdout and stderr
            result = subprocess.run(
                ["kubectl", "apply", "-f", f.name],
                # check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Check if there was an error
            if result.returncode != 0:
                print("Error encountered:")
                # Prettify and print the stderr
                pprint(result.stderr)
                exit(1)
            else:
                print("Output:")
                # Prettify and print the stdout
                print(result.stdout)

                if "created" in result.stdout:
                  print(f"\033[1m\033[92m\033[48;5;22m✔✔✔ JOB {args.name} HAS BEEN SUBMITTED SUCCESSFULLY. ✔✔✔\033[0m")
                  print(f"\033[1m\033[92m\033[48;5;22m✔✔✔ IMAGE USED: {args.image} ✔✔✔\033[0m")
                elif "unchanged" in result.stdout:
                  print(f"\033[1m\033[91m\033[48;5;52m--- JOB {args.name} ALREADY EXISTS. ---\033[0m")
                  print(f"To delete it, run:\n  runai delete job {args.name}")

                print("\nThe following commands may come in handy:")
                print(
                    f"runai exec {args.name} -it zsh # opens an interactive shell on the pod"
                )
                print(
                    f"runai delete job {args.name} # kills the job and removes it from the list of jobs"
                )
                print(
                    f"runai describe job {args.name} # shows information on the status/execution of the job"
                )
                print("runai list jobs # list all jobs and their status")
                print(f"runai logs {args.name} # shows the output/logs for the job")
