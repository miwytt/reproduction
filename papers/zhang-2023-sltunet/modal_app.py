"""SLTUNET (Zhang et al., ICLR 2023) reproduction on Modal.

Runs the authors' published inference path at the pinned upstream commit against the
PHOENIX-2014T test split, using the authors' released SMKD sign-embedding model and
checkpoint-averaged SLTUNET model, then scores with the repository's own metric code.

This verifies the released artifact and our evaluation pipeline. It does not reproduce
the authors' training.
"""

import json
import os
import subprocess

import modal

PAPER_ID = "zhang-2023-sltunet"
UPSTREAM = "https://github.com/bzhangGo/sltunet.git"
UPSTREAM_COMMIT = "b1d1d0e8b3b7275e10cd89229f2632b556df5de9"
RELEASE_URL = "https://data.statmt.org/bzhang/iclr2023_sltunet/phoenix.tar.gz"
RELEASE_SHA256 = "b0e708b7abe5689475905ad11ac578abb02eb0f9bf00b207bbd6d4342afe5152"

# TF 1.15 needs CUDA 10, which supports Turing (SM75) but not Ampere or later, so this
# runs on T4. The NGC tf1 images would allow newer GPUs but nvcr.io requires credentials.
GPU = "T4"

image = (
    modal.Image.from_registry(
        "tensorflow/tensorflow:1.15.5-gpu-py3", add_python=None
    )
    # The 2019-era base image pins NVIDIA apt repos whose signing key NVIDIA rotated in
    # 2022, so apt-get update fails with "no longer signed" (exit 100). The CUDA runtime
    # is already baked into the image; these lists are only needed to install more CUDA
    # packages, which this reproduction does not do.
    .run_commands(
        "rm -f /etc/apt/sources.list.d/cuda.list "
        "/etc/apt/sources.list.d/nvidia-ml.list"
    )
    .apt_install("git", "wget", "ffmpeg", "libsm6", "libxext6", "libgl1-mesa-glx")
    .pip_install(
        "torch==1.7.1+cu101",
        "torchvision==0.8.2+cu101",
        extra_index_url="https://download.pytorch.org/whl/torch_stable.html",
    )
    .pip_install(
        "opencv-python-headless==4.6.0.66",
        "pyyaml==5.4.1",
        "tqdm==4.64.1",
        "portalocker==2.7.0",
    )
)

app = modal.App(f"{PAPER_ID}-inference", image=image)

datasets = modal.Volume.from_name("datasets")
hf_cache = modal.Volume.from_name("huggingface-cache")
results = modal.Volume.from_name(f"{PAPER_ID}-results", create_if_missing=True)

VOLUMES = {
    "/datasets": datasets,
    "/cache/huggingface": hf_cache,
    "/results": results,
}
ENV = {
    "HF_HOME": "/cache/huggingface",
    "HF_HUB_CACHE": "/cache/huggingface/hub",
}

PHOENIX = "/datasets/rwth-phoenix-2014-t"


def _sh(cmd, cwd=None, check=True):
    print(f"+ {cmd}", flush=True)
    proc = subprocess.run(cmd, shell=True, cwd=cwd, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {cmd}")
    return proc.returncode


def _prepare_upstream():
    """Clone the pinned upstream and unpack the released artifacts (cached in /results)."""
    work = "/work"
    os.makedirs(work, exist_ok=True)
    src = f"{work}/sltunet"
    if not os.path.exists(src):
        _sh(f"git clone --quiet {UPSTREAM} {src}")
        _sh(f"git checkout --quiet {UPSTREAM_COMMIT}", cwd=src)
    head = subprocess.run(
        "git rev-parse HEAD", shell=True, cwd=src, capture_output=True, text=True
    ).stdout.strip()
    assert head == UPSTREAM_COMMIT, f"upstream commit mismatch: {head}"

    tarball = "/results/artifacts/phoenix.tar.gz"
    os.makedirs("/results/artifacts", exist_ok=True)
    if not os.path.exists(tarball):
        _sh(f"wget -q -O {tarball} {RELEASE_URL}")
        results.commit()
    digest = subprocess.run(
        f"sha256sum {tarball}", shell=True, capture_output=True, text=True
    ).stdout.split()[0]
    assert digest == RELEASE_SHA256, f"release tarball sha256 mismatch: {digest}"

    release = f"{work}/release"
    if not os.path.exists(release):
        os.makedirs(release, exist_ok=True)
        _sh(f"tar xzf {tarball} -C {release}")
    return src, release, head, digest


def _build_inputs(release, limit=None):
    """Map the authors' released test list onto the MP4s in the shared Volume.

    The released test.txt points at the original PNG frame directories, which the shared
    Volume does not hold; it holds MP4 re-encodings. The authors' own data loader reads
    either (dataloader_video.BaseFeeder branches on the suffix), so only the path list
    changes, not the code. Order is preserved exactly from the released list so that the
    reference order matches.
    """
    with open(f"{release}/test.txt") as handle:
        released = [line.strip() for line in handle if line.strip()]

    # Each released line is ".../<sequence-name>/*.png"; take the directory component.
    names = [line.rsplit("/", 1)[0].rsplit("/", 1)[-1] for line in released]

    refs = {}
    with open(f"{PHOENIX}/annotations/PHOENIX-2014-T.test.corpus.csv") as handle:
        header = handle.readline().rstrip("\n").split("|")
        name_i, trans_i = header.index("name"), header.index("translation")
        for line in handle:
            parts = line.rstrip("\n").split("|")
            refs[parts[name_i]] = parts[trans_i].strip()

    rows = []
    missing_video, missing_ref = [], []
    for name in names:
        video = f"{PHOENIX}/videos/test/{name}.mp4"
        if not os.path.exists(video):
            missing_video.append(name)
            continue
        if name not in refs:
            missing_ref.append(name)
            continue
        rows.append((name, video, refs[name]))

    print(f"released list: {len(released)}; usable: {len(rows)}")
    if missing_video:
        print(f"missing video ({len(missing_video)}): {missing_video[:5]}")
    if missing_ref:
        print(f"missing reference ({len(missing_ref)}): {missing_ref[:5]}")

    if limit:
        rows = rows[:limit]
    return rows


@app.function(
    gpu=GPU, volumes=VOLUMES, timeout=60 * 60 * 6, cpu=8.0, memory=32768
)
def infer(limit: int = None, tag: str = "full"):
    import time

    os.environ.update(ENV)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    src, release, head, digest = _prepare_upstream()
    rows = _build_inputs(release, limit=limit)

    run_dir = f"/results/runs/{tag}"
    os.makedirs(run_dir, exist_ok=True)

    list_file = f"{run_dir}/inputs.txt"
    ref_file = f"{run_dir}/reference.de"
    with open(list_file, "w") as handle:
        handle.write("\n".join(video for _, video, _ in rows) + "\n")
    with open(ref_file, "w") as handle:
        handle.write("\n".join(ref for _, _, ref in rows) + "\n")

    ckpt = f"{release}/sltunet_ckpt"
    # Invoke the authors' pinned entry point with their released configuration
    # (sltunet_ckpt/param.json, infer.sh); only paths are substituted.
    cmd = (
        "python3 run.py --mode infer --parameters="
        "max_len=256,max_img_len=512,eval_batch_size=4,"
        "beam_size=8,remove_bpe=True,decode_alpha=1.0,"
        "gpus=[0],"
        "eval_task='sign2text',"
        f'src_codes="{ckpt}/ende.bpe",tgt_codes="{ckpt}/ende.bpe",'
        f'src_vocab_file="{ckpt}/vocab.zero.drop",'
        f'tgt_vocab_file="{ckpt}/vocab.zero.drop",'
        f'output_dir="{ckpt}",'
        f'test_output="{run_dir}/trans.txt",'
        f'img_test_file="{list_file}",'
        f'gloss_path="{release}/phoenix2014/gloss_dict.npy",'
        f'sign_cfg="{release}/baseline.yaml",'
        f'smkd_model_path="{release}/signemb_ckpt/average.pt",'
    )
    exit_code = _sh(cmd, cwd=src, check=False)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    scores = {}
    trans = f"{run_dir}/trans.txt"
    if os.path.exists(trans):
        proc = subprocess.run(
            f"python3 eval/metrics.py -t slt -hyp {trans} -ref {ref_file}",
            shell=True, cwd=src, capture_output=True, text=True,
        )
        print(proc.stdout, proc.stderr, flush=True)
        scores["metrics_stdout"] = proc.stdout
        scores["metrics_stderr"] = proc.stderr[-4000:]

    meta = {
        "paper_id": PAPER_ID,
        "tag": tag,
        "command": cmd,
        "exit_code": exit_code,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "upstream_commit": head,
        "release_sha256": digest,
        "gpu": GPU,
        "n_sequences": len(rows),
        "scores": scores,
    }
    with open(f"{run_dir}/run.json", "w") as handle:
        json.dump(meta, handle, indent=2)
    results.commit()
    print(json.dumps(meta, indent=2)[:4000], flush=True)
    return meta


@app.function(volumes=VOLUMES, timeout=60 * 30)
def probe():
    """Cheap environment and data probe: no GPU, no model."""
    os.environ.update(ENV)
    src, release, head, digest = _prepare_upstream()
    rows = _build_inputs(release)
    import cv2

    name, video, ref = rows[0]
    cap = cv2.VideoCapture(video)
    frames = 0
    ok, _ = cap.read()
    while ok:
        frames += 1
        ok, _ = cap.read()
    out = {
        "upstream_commit": head,
        "release_sha256": digest,
        "sequences_mapped": len(rows),
        "first_sequence": name,
        "first_sequence_frames_decoded": frames,
        "first_reference": ref,
        "cv2": cv2.__version__,
    }
    print(json.dumps(out, indent=2), flush=True)
    return out
