# lts4-base

Shared LTS4 GPU image (CUDA 12.9 + cudnn). Per-user setup runs in `utils/entrypoint.sh` at job start. Should work for any epfl member, with the pixi binary installed in the image itself, and since pixi environemnts are stored in project folders (on scratch), is a good starting point if you just need to install different python environments.

- **Pixi** is installed at build time in `/opt/pixi/bin` (no scratch install, no `.pixi` symlink required).
- **Conda** is not baked into the image; add a symlink entry in `symlinks.json` to install Miniconda on scratch at first job start and point to it in the pod home.

Example `symlinks.json` for conda users:

```json
{
	"miniconda3": ["conda", "miniconda3"]
}
```

Build and push (no need if you do not plan to change anything about the dockerfile, you can just use the pre-built image.):

```bash
source ~/.profile
./scripts/publish.sh --path=dockerfiles/lts4-base --img=lts4-base --version=1 --push=True
```