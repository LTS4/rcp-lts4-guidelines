import argparse
import os
import shlex
import subprocess

from termcolor import colored

parser = argparse.ArgumentParser(description="Launch a job on Run:AI")

parser.add_argument("--name", type=str, help="Name of the job", required=True)
parser.add_argument("--image", type=str, help="Docker image to run", default=-1)
parser.add_argument("--interactive", action="store_true", help="Run an interactive job")
parser.add_argument("--command", type=str, help="Command to run. For an interactive job, 'sleep infinity' is used")
parser.add_argument("--gpus", type=float, help="Number of GPUs", default=0.0)
parser.add_argument("--cpus", type=float, help="Number of CPUs", default=None)
parser.add_argument("--mem", type=int, help="RAM memory size (in GB)", default=100)
parser.add_argument("--noshm", action="store_true", help="Do not use shared memory")
parser.add_argument("--student", action="store_true", help="Use student paths")
parser.add_argument("--dry", action="store_true", help="Dry run")
parser.add_argument(
    "--node-pool", type=str, help="Node pool to use", default="v100", choices=["default", "v100", "a100"]
)


def main(args):
    uid = os.getenv("EPFL_UID")
    gid = os.getenv("EPFL_GID")
    supplementary_groups = os.getenv("EPFL_SUPPLEMENTAL_GROUPS")
    user = os.getenv("EPFL_USER")
    assert user is not None, "EPFL_USER must be set"
    assert uid is not None, "EPFL_UID must be set"
    assert gid is not None, "EPFL_GID must be set"
    if not args.student:
        assert supplementary_groups is not None, "EPFL_SUPPLEMENTAL_GROUPS must be set"
    args.uid = int(uid)
    args.gid = int(gid)
    args.user = user
    if supplementary_groups is not None:
        args.supplemental_groups = int(supplementary_groups)

    if args.student:
        args.virtual_home = "/mnt/lts4/scratch/students"
        args.supplemental_groups = ""
    else:
        args.virtual_home = "/mnt/lts4/scratch/home"
        args.supplemental_groups = f"--supplemental-groups {args.supplemental_groups} \\"

    if args.gpus == int(args.gpus):
        args.gpus = int(args.gpus)

    if args.interactive:
        args.command = "--interactive  -- sleep infinity"
    else:
        assert args.command is not None, "Command must be provided for non-interactive jobs"
        args.command = "cd $VIRTUAL_HOME && " + args.command
        args.command = f'--command -- /bin/bash -c "{args.command}"'

    args.shm = "--large-shm \\"
    if args.noshm:
        args.shm = ""

    if args.cpus is None:
        args.cpus = ""
    else:
        args.cpus = f"--cpu {args.cpus} \\"

    config = config_template.format(**vars(args))
    config = "".join([s for s in config.strip().splitlines(True) if s.strip("\r\n").strip()]) + "\n"
    print(colored(config, "grey", force_color=True))
    if not args.dry:
        config_args = shlex.split(config)
        result = subprocess.run(config_args, capture_output=True)
        print(result.stdout.decode("utf-8"))
        print(result.stderr.decode("utf-8"))

    print(colored(useful_commands.format(**vars(args), empt=" " * len(args.name)), "blue"))


config_template = """
runai submit \\
  --name {name} \\
  -i {image} \\
  --gpu {gpus} \\
  {cpus}
  {shm}
  -e VIRTUAL_HOME={virtual_home}/{user} \\
  -e DATA_DIR=/mnt/lts4/scratch/data \\
  -e WANDB_API_KEY=SECRET:wandb-secret,secret \\
  --node-pool {node_pool} \\
  --run-as-uid {uid} \\
  --run-as-gid {gid} \\
  {supplemental_groups}
  --existing-pvc claimname=lts4-scratch,path=/mnt/lts4/scratch \\
  {command}
"""

useful_commands = """The following commands may come in handy:
  runai bash {name}          \t\t# opens an interactive shell on the pod
  runai delete job {name}    \t\t# kills the job and removes it from the list of jobs
  runai describe job {name}  \t\t# shows information on the status/execution of the job
  runai list jobs {empt}     \t\t# list all jobs and their status
  runai logs {name}          \t\t# shows the output/logs for the job
"""

if __name__ == "__main__":
    args = parser.parse_args()
    result = subprocess.run(["runai", "list"], capture_output=True)
    if any([r.split()[0] == args.name for r in result.stdout.decode("utf-8").split("\n") if len(r) > 0]):
        print(colored(f"Job {args.name} already exists. Delete it first or change the name.", "red"))
        exit(1)
    assert (
        args.image != -1 or os.getenv("EPFL_IMAGE") is not None
    ), "EPFL image must be set either as an argument or as an environment variable"
    if args.image == -1:
        print("Using EPFL_IMAGE environment variable: ", os.getenv("EPFL_IMAGE"))
        args.image = os.getenv("EPFL_IMAGE")
    main(args)
