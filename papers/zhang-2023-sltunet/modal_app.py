"""SLTUNET (Zhang et al., ICLR 2023) reproduction on Modal.

Runs the authors' published inference path at the pinned upstream commit against the
PHOENIX-2014T test split, using their released SMKD sign-embedding model and
checkpoint-averaged SLTUNET model, then scores with the repository's own metric code.

This verifies the released artifact and our evaluation pipeline. It does not reproduce
the authors' training.

The work runs in a Modal Sandbox rather than a Modal Function: the container is
TensorFlow 1.15 on Python 3.6, and Modal's in-container runtime requires Python >= 3.9.
A Sandbox executes the command directly, so the legacy interpreter is never asked to
host Modal's runtime. `add_python` is not an option here because the base image already
owns /usr/local/bin/python and the injected interpreter collides with it.

Usage (always through the workspace wrapper, from the repository root):
  .agents/skills/reproduce-paper/scripts/modal_repro_sign.sh \
      run papers/zhang-2023-sltunet/modal_app.py --limit 8 --tag preflight
"""

from pathlib import Path

import modal

PAPER_ID = "zhang-2023-sltunet"

# TF 1.15 is CUDA 10, which supports Turing (SM75) but not Ampere or later, so T4.
# The NGC tf1 images would lift that limit but nvcr.io returns 401 anonymously and
# registry credentials are a secrets gate.
GPU = "T4"

image = (
    modal.Image.from_registry("tensorflow/tensorflow:1.15.5-gpu-py3")
    # The 2019-era base pins NVIDIA apt repos whose signing key NVIDIA rotated in 2022,
    # so apt-get update fails with "no longer signed" (exit 100). The CUDA runtime is
    # already in the image; these lists only matter for installing more CUDA packages.
    .run_commands(
        "rm -f /etc/apt/sources.list.d/cuda.list "
        "/etc/apt/sources.list.d/nvidia-ml.list"
    )
    .apt_install(
        "git", "wget", "ffmpeg", "libsm6", "libxext6", "libgl1-mesa-glx",
        # Toolchain for building ctcdecode, a C++ PyTorch extension.
        "build-essential", "cmake",
    )
    # torch_stable.html is a find-links page, not a PEP 503 index, so it needs -f;
    # --extra-index-url cannot resolve the +cu101 local-version wheels.
    .run_commands(
        "python -m pip install --no-cache-dir "
        "torch==1.7.1+cu101 torchvision==0.8.2+cu101 "
        "-f https://download.pytorch.org/whl/torch_stable.html",
        "python -m pip install --no-cache-dir "
        "opencv-python-headless==4.6.0.66 pyyaml==5.4.1 tqdm==4.64.1",
        # Undeclared upstream dependency: smkd/utils/decode.py imports ctcdecode, but
        # the repository README lists only python and tensorflow. It is a C++ extension
        # published on GitHub rather than PyPI, so it is pinned by commit. Installing a
        # missing dependency is environment work, not a patch to the authors' code.
        "python -m pip install --no-cache-dir "
        "git+https://github.com/parlance/ctcdecode.git"
        "@c90ad94a0b19554f80804fb7812f2a1447a34a70",
        # Remaining undeclared upstream dependencies on the inference path, found by
        # scanning every import in the repository rather than discovering them one
        # failed run at a time: pyarrow (smkd/dataset/dataloader_video.py), h5py
        # (smkd/seq_scripts.py, data.py), scipy (smkd/utils/video_augmentation.py) and
        # portalocker (eval/sacrebleu.py). Versions are the last ones publishing cp36
        # wheels. pandas, sign_language_datasets and tensorflow_datasets are imported
        # only by the preprocessing and DGS3-T scripts, and jactorch is guarded by a
        # try/except with a vendored fallback, so none of those are installed.
        "python -m pip install --no-cache-dir "
        "pyarrow==6.0.1 h5py==2.10.0 scipy==1.5.4 portalocker==2.0.0",
    )
    # Resolved against this file, not the caller's cwd, so the wrapper can be invoked
    # from the repository root.
    .add_local_file(
        str(Path(__file__).parent / "run_inference.py"),
        "/opt/run_inference.py",
        copy=True,
    )
)

app = modal.App(f"{PAPER_ID}-inference")

datasets = modal.Volume.from_name("datasets")
hf_cache = modal.Volume.from_name("huggingface-cache")
results = modal.Volume.from_name(f"{PAPER_ID}-results", create_if_missing=True)


@app.local_entrypoint()
def main(limit: int = 0, tag: str = "preflight", timeout_s: int = 6 * 60 * 60):
    sandbox = modal.Sandbox.create(
        "bash",
        "-lc",
        f"python /opt/run_inference.py --tag {tag} --limit {limit}",
        app=app,
        image=image,
        gpu=GPU,
        cpu=8.0,
        memory=32768,
        timeout=timeout_s,
        volumes={
            "/datasets": datasets,
            "/cache/huggingface": hf_cache,
            "/results": results,
        },
        # Required by the study's Modal conventions even where unused by this path.
        secrets=[],
        env={
            "HF_HOME": "/cache/huggingface",
            "HF_HUB_CACHE": "/cache/huggingface/hub",
        },
    )
    print(f"sandbox: {sandbox.object_id}")
    for line in sandbox.stdout:
        print(line, end="")
    stderr = sandbox.stderr.read()
    sandbox.wait()
    if stderr.strip():
        print("=== STDERR (tail) ===")
        print(stderr[-8000:])
    print(f"sandbox {sandbox.object_id} returncode={sandbox.returncode}")
