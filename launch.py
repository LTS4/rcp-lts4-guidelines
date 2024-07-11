import argparse
import os
import subprocess
import tempfile

import yaml
from termcolor import colored

default_values = yaml.safe_load(open(".config/info.yaml"))

parser = argparse.ArgumentParser(description="Launch a job on Run:AI")

parser.add_argument("--name", type=str, help="Name of the job", required=True)
parser.add_argument("--user", type=str, help="User name", default=default_values["user"])
parser.add_argument("--uid", type=int, help="User ID", default=default_values["uid"])
parser.add_argument("--gid", type=int, help="Group ID", default=default_values["gid"])
parser.add_argument("--image", type=str, help="Docker image to run", default=default_values["image"])
parser.add_argument("--pvc", type=str, help="Persistent Volume Claim", default=default_values["pvc"])
parser.add_argument("--mount_path", type=str, help="Path to mount the PVC", default=default_values["mount_path"])

#
parser.add_argument("--workdir", type=str, help="Working directory", default="/workdir")
parser.add_argument("--interactive", action="store_true", help="Run an interactive job")
parser.add_argument("--command", type=str, help="Command to run. For an interactive job, 'sleep infinity' is used")
parser.add_argument("--gpus", type=float, help="Number of GPUs", default=0.0)
parser.add_argument("--cpus", type=int, help="Number of CPUs", default=10)
parser.add_argument("--mem", type=int, help="RAM memory size (in GB)", default=100)
parser.add_argument(
    "--shm", type=int, help="Size of Shared Memory (in GB). If None, it is not specified.", default=None
)

#
parser.add_argument("--dry", action="store_true", help="Dry run")


def main(args):
    if args.interactive:
        args.command = "sleep infinity"
        args.interactive_label = (
            'priorityClassName: "build" # Interactive Job if present, for Train Job REMOVE this line'
        )
        args.kind_job = "InteractiveWorkload"
    else:
        assert args.command is not None, "Command must be provided for non-interactive jobs"
        args.interactive_label = ""
        args.kind_job = "TrainingWorkload"

    if args.workdir is None:
        args.workdir = os.path.join(args.mount_path, "home", args.user)
        print(f"Setting workdir to virtual home directory in scratch: {args.workdir}")

    if args.shm is not None:
        assert args.shm > 0, "Shared memory size must be positive"
        args.shm_volume = """- name: dshm
        emptyDir:
          medium: Memory
          sizeLimit: {shm}Gi  # specify the number in gigabytes""".format(
            shm=args.shm
        )
        args.shm_mount = """- mountPath: /dev/shm
          name: dshm"""
    else:
        args.shm_volume = ""
        args.shm_mount = ""

    config = config_template.format(**vars(args))
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config)
        f.flush()
        print(f"Config written to {f.name}")

        if args.dry:
            print(colored(config, "black", force_color=True))
            pass
        else:
            result = subprocess.run(["kubectl", "apply", "-f", f.name], capture_output=True)
            print(result.stdout.decode("utf-8"))
            print(result.stderr.decode("utf-8"))

        if not args.dry:
            print(colored(useful_commands.format(**vars(args), empt=" " * len(args.name)), "blue"))
        else:
            print("k apply -f", f.name)


config_template = """
apiVersion: run.ai/v1
kind: RunaiJob #{kind_job}
metadata:
  name: {name}
  labels:
    {interactive_label}
    user: {user}
    PreviousJob: "true"
spec:
  template:
    metadata:
      labels:
        user: {user}
        release: {name} # MUST BE SAME NAME of your pod "name" specify in the metadata above in order to get logs into the Run:AI dashboard
    spec:
      schedulerName: runai-scheduler
      restartPolicy: Never
      securityContext:
        runAsUser: {uid}
        runAsGroup: {gid}
        fsGroup: {gid} # This is same as gid (runAsGroup)
      containers:
      - name: container-name
        image: {image}
        imagePullPolicy: Always
        workingDir: {workdir}
        command: ["/bin/bash", "-c"]
        args:
        - "cd $VIRTUAL_HOME && {command}" 

        env:
        - name: WANDB_API_KEY
          valueFrom:
            secretKeyRef:
              name: wandb-secret # The name of the secret
              key: secret # The key to fetch from the secret
        - name: VIRTUAL_HOME
          value: {mount_path}/home/{user}

        resources:
          requests:
            cpu: {cpus}
            memory: {mem}Gi
            nvidia.com/gpu: {gpus}
          limits:
            cpu: {cpus}
            memory: {mem}Gi
            nvidia.com/gpu: {gpus}

        volumeMounts:
        - mountPath: {mount_path}
          name: scratch-data 
        {shm_mount}
      volumes:
      - name: scratch-data 
        persistentVolumeClaim:
          claimName: {pvc} # Name of the PVC you can get
      {shm_volume}
      
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
    main(args)
