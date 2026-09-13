"""Runs inside the TensorFlow 1.15 container (Python 3.6). Invoked by modal_app.py.

Clones the pinned upstream, unpacks the authors' released artifacts, maps the released
test list onto the sign videos in the shared Volume, runs the authors' published
inference entry point, and scores the output with the repository's own metric code.
"""

from __future__ import print_function

import argparse
import json
import os
import subprocess
import sys
import time

UPSTREAM = "https://github.com/bzhangGo/sltunet.git"
UPSTREAM_COMMIT = "b1d1d0e8b3b7275e10cd89229f2632b556df5de9"
RELEASE_URL = "https://data.statmt.org/bzhang/iclr2023_sltunet/phoenix.tar.gz"
RELEASE_SHA256 = "b0e708b7abe5689475905ad11ac578abb02eb0f9bf00b207bbd6d4342afe5152"
PHOENIX = "/datasets/rwth-phoenix-2014-t"


def sh(cmd, cwd=None, check=True):
    print("+ " + cmd)
    sys.stdout.flush()
    code = subprocess.call(cmd, shell=True, cwd=cwd)
    if check and code != 0:
        raise RuntimeError("command failed (%d): %s" % (code, cmd))
    return code


def prepare():
    src = "/work/sltunet"
    if not os.path.exists(src):
        sh("mkdir -p /work")
        sh("git clone --quiet %s %s" % (UPSTREAM, src))
        sh("git checkout --quiet %s" % UPSTREAM_COMMIT, cwd=src)
    head = subprocess.check_output(
        "git rev-parse HEAD", shell=True, cwd=src
    ).decode().strip()
    assert head == UPSTREAM_COMMIT, "upstream commit mismatch: %s" % head

    tarball = "/results/artifacts/phoenix.tar.gz"
    sh("mkdir -p /results/artifacts")
    if not os.path.exists(tarball):
        sh("wget -q -O %s %s" % (tarball, RELEASE_URL))
    digest = subprocess.check_output(
        "sha256sum %s" % tarball, shell=True
    ).decode().split()[0]
    assert digest == RELEASE_SHA256, "release sha256 mismatch: %s" % digest

    release = "/work/release"
    if not os.path.exists(release):
        sh("mkdir -p %s" % release)
        sh("tar xzf %s -C %s" % (tarball, release))
    return src, release, head, digest


def build_inputs(release, limit):
    """Map the released PNG-frame test list onto the Volume's MP4s, preserving order.

    The authors' loader (smkd/dataset/dataloader_video.py) branches on the path suffix
    and opens non-PNG paths with cv2.VideoCapture, so only the path list changes.
    """
    with open(release + "/test.txt") as handle:
        released = [line.strip() for line in handle if line.strip()]
    names = [line.rsplit("/", 1)[0].rsplit("/", 1)[-1] for line in released]

    refs = {}
    ann = PHOENIX + "/annotations/PHOENIX-2014-T.test.corpus.csv"
    with open(ann) as handle:
        header = handle.readline().rstrip("\n").split("|")
        ni, ti = header.index("name"), header.index("translation")
        for line in handle:
            parts = line.rstrip("\n").split("|")
            if len(parts) > max(ni, ti):
                refs[parts[ni]] = parts[ti].strip()

    rows, missing_video, missing_ref = [], [], []
    for name in names:
        video = "%s/videos/test/%s.mp4" % (PHOENIX, name)
        if not os.path.exists(video):
            missing_video.append(name)
        elif name not in refs:
            missing_ref.append(name)
        else:
            rows.append((name, video, refs[name]))

    print("released list: %d; mapped: %d" % (len(released), len(rows)))
    if missing_video:
        print("missing video (%d): %s" % (len(missing_video), missing_video[:5]))
    if missing_ref:
        print("missing reference (%d): %s" % (len(missing_ref), missing_ref[:5]))
    if limit:
        rows = rows[:limit]
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="full")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    src, release, head, digest = prepare()
    rows = build_inputs(release, args.limit)

    run_dir = "/results/runs/" + args.tag
    sh("mkdir -p %s" % run_dir)
    list_file = run_dir + "/inputs.txt"
    ref_file = run_dir + "/reference.de"
    with open(list_file, "w") as handle:
        handle.write("\n".join(r[1] for r in rows) + "\n")
    with open(ref_file, "w") as handle:
        handle.write("\n".join(r[2] for r in rows) + "\n")

    ckpt = release + "/sltunet_ckpt"
    trans = run_dir + "/trans.txt"
    # The authors' pinned entry point with their released configuration (infer.sh /
    # param.json); only paths are substituted.
    cmd = (
        "python run.py --mode infer --parameters="
        "max_len=256,max_img_len=512,eval_batch_size=4,"
        "beam_size=8,remove_bpe=True,decode_alpha=1.0,"
        "gpus=[0],"
        "eval_task='sign2text',"
        'src_codes="{c}/ende.bpe",tgt_codes="{c}/ende.bpe",'
        'src_vocab_file="{c}/vocab.zero.drop",'
        'tgt_vocab_file="{c}/vocab.zero.drop",'
        'output_dir="{c}",'
        'test_output="{t}",'
        'img_test_file="{l}",'
        'gloss_path="{r}/phoenix2014/gloss_dict.npy",'
        'sign_cfg="{r}/baseline.yaml",'
        'smkd_model_path="{r}/signemb_ckpt/average.pt",'
    ).format(c=ckpt, t=trans, l=list_file, r=release)

    exit_code = sh(cmd, cwd=src, check=False)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    metrics = ""
    scored = run_dir + "/trans.debpe.txt"
    if os.path.exists(trans):
        # --mode infer writes translations through evalu.dump_tanslation, which does not
        # apply remove_bpe; upstream only strips BPE inside evalu.eval_metric, which this
        # path never calls. Scoring the raw file counts "@@ " markers as wrong tokens
        # (177 of 642 lines on the test split, worth about 5.5 BLEU). Reproduce upstream's
        # own transformation exactly: evalu.eval_metric does line.replace("@@ ", "") on
        # both hypotheses and references before scoring.
        with open(trans) as handle:
            raw = handle.read()
        with open(scored, "w") as handle:
            handle.write(raw.replace("@@ ", ""))
        proc = subprocess.Popen(
            "python eval/metrics.py -t slt -hyp %s -ref %s" % (scored, ref_file),
            shell=True, cwd=src, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        metrics = proc.communicate()[0].decode("utf-8", "replace")
        print("=== METRICS ===")
        print(metrics)

    meta = {
        "tag": args.tag,
        "command": cmd,
        "exit_code": exit_code,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "upstream_commit": head,
        "release_sha256": digest,
        "n_sequences": len(rows),
        "metrics_output": metrics,
        "frame_source": "lossy HEVC re-encodings from the shared Volume, not original PNG frames",
    }
    with open(run_dir + "/run.json", "w") as handle:
        json.dump(meta, handle, indent=2)
    print("=== RUNJSON ===")
    print(json.dumps(meta, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
