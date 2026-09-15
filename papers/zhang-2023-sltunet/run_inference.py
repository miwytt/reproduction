"""Runs inside the TensorFlow 1.15 container (Python 3.6). Invoked by modal_app.py.

Clones the pinned upstream, unpacks the authors' released artifacts, maps the released
test list onto the sign videos in the shared Volume, runs the authors' published
inference entry point, and scores the output with the repository's own metric code.
"""

from __future__ import print_function

import argparse
import glob
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
RWTH_ARCHIVE = ("https://www-i6.informatik.rwth-aachen.de/ftp/pub/"
                "rwth-phoenix/2016/phoenix-2014-T.v3.tar.gz")


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


def build_inputs(release, limit, frame_source="video", split="test"):
    """Build the decoder's input list, preserving the authors' released test order.

    frame_source='png' is the faithful path: the released test.txt already contains the
    authors' own file list as
    PHOENIX-2014-T-release-v3/PHOENIX-2014-T/features/fullFrame-210x260px/test/<seq>/*.png,
    so the only change is prefixing the Volume location of that distribution. Nothing about
    the list is reconstructed.

    frame_source='video' substitutes the Volume's HEVC re-encodings instead. The authors'
    loader (smkd/dataset/dataloader_video.py) branches on the path suffix and opens non-PNG
    paths with cv2.VideoCapture, so that too is a path substitution rather than a patch, but
    it feeds the encoder lossy pixels.
    """
    ann = "%s/annotations/PHOENIX-2014-T.%s.corpus.csv" % (PHOENIX, split)
    if split == "test":
        # Use the authors' own released ordering for the split they published it for.
        with open(release + "/test.txt") as handle:
            released = [line.strip() for line in handle if line.strip()]
        names = [l.rsplit("/", 1)[0].rsplit("/", 1)[-1] for l in released]
    else:
        # No released list exists for dev; take the annotation CSV order. References come
        # from the same file, so hypothesis/reference alignment is guaranteed either way.
        names, released = [], []
        with open(ann) as handle:
            hdr = handle.readline().rstrip("\n").split("|")
            ni = hdr.index("name")
            for line in handle:
                parts = line.rstrip("\n").split("|")
                if len(parts) > ni:
                    names.append(parts[ni])
                    released.append(
                        "PHOENIX-2014-T-release-v3/PHOENIX-2014-T/features/"
                        "fullFrame-210x260px/%s/%s/*.png" % (split, parts[ni]))

    refs = {}
    with open(ann) as handle:
        header = handle.readline().rstrip("\n").split("|")
        ni, ti = header.index("name"), header.index("translation")
        for line in handle:
            parts = line.rstrip("\n").split("|")
            if len(parts) > max(ni, ti):
                refs[parts[ni]] = parts[ti].strip()

    rows, missing_video, missing_ref = [], [], []
    for name, released_path in zip(names, released):
        if frame_source == "png":
            # The authors' own path, rooted at the Volume copy of the distribution.
            source = "%s/raw/%s" % (PHOENIX, released_path)
            present = bool(glob.glob(source))
        else:
            source = "%s/videos/%s/%s.mp4" % (PHOENIX, split, name)
            present = os.path.exists(source)
        if not present:
            missing_video.append(name)
        elif name not in refs:
            missing_ref.append(name)
        else:
            rows.append((name, source, refs[name]))

    print("frame_source: %s" % frame_source)
    print("released list: %d; mapped: %d" % (len(released), len(rows)))
    if missing_video:
        print("missing frames (%d): %s" % (len(missing_video), missing_video[:5]))
    if missing_ref:
        print("missing reference (%d): %s" % (len(missing_ref), missing_ref[:5]))
    if limit:
        rows = rows[:limit]
    return rows



def stage_frames(rows):
    """Put the needed PNG sequences on container-local disk before decoding.

    Two routes, because the obvious one does not work. Copying from the Volume is
    pathological: cold reads measured 186 ms per file, and a 32-way parallel cp over the
    ~96,000 files of the test split made no measurable progress in 1.5 hours, so the FUSE
    mount evidently degrades under concurrent small reads rather than overlapping them.

    The working route streams the original RWTH archive straight into tar and extracts only
    the frame tree, which is one sequential network read instead of ~96,000 random ones. The
    bytes are identical to the Volume copy; this is purely how they are fetched.

    Falls back to copying from the Volume if the archive is unreachable.
    """
    local_root = "/work/frames"
    marker = local_root + "/.staged"
    if os.path.exists(marker):
        print("frames already staged at %s" % local_root)
    else:
        sh("mkdir -p %s" % local_root)
        t0 = time.time()
        # Only the frame tree, and only the splits this run needs.
        # 5 components precede <seq>/: release / PHOENIX-2014-T / features /
        # fullFrame-210x260px / test. Stripping 4 would leave a stray "test/"
        # level and the staged-path lookup below would find nothing.
        wildcard = "*/features/fullFrame-210x260px/test/*"
        # wget, not curl: this image is Ubuntu 18.04 whose curl 7.58 predates
        # --retry-all-errors, and the flag error made the whole route fail instantly.
        rc = sh(
            "wget -q -O- --tries=5 --waitretry=20 %s "
            "| tar xz -C %s --wildcards --strip-components=5 '%s'"
            % (RWTH_ARCHIVE, local_root, wildcard), check=False)
        print("archive stage rc=%d in %.1f s" % (rc, time.time() - t0))
        if rc != 0:
            print("archive route failed; falling back to Volume copy")
            dirs = sorted({os.path.dirname(src) for _, src, _ in rows})
            listing = "/work/stage_dirs.txt"
            with open(listing, "w") as handle:
                handle.write("\n".join(dirs) + "\n")
            sh("xargs -a %s -P 16 -I{} cp -r {} %s/" % (listing, local_root))
        open(marker, "w").close()

    staged = []
    missing = []
    for name, src, ref in rows:
        seq = os.path.basename(os.path.dirname(src))
        pattern = "%s/%s/*.png" % (local_root, seq)
        if not glob.glob(pattern):
            missing.append(seq)
            continue
        staged.append((name, pattern, ref))
    total = sum(len(glob.glob(p)) for _, p, _ in staged)
    print("staged %d/%d sequences, %d frames" % (len(staged), len(rows), total))
    if missing:
        raise RuntimeError("staging missing %d sequences, e.g. %s"
                           % (len(missing), missing[:5]))
    return staged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="full")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--split", default="test", choices=["test", "dev"])
    parser.add_argument("--frame-source", default="video",
                        choices=["video", "png"])
    args = parser.parse_args()

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    src, release, head, digest = prepare()
    rows = build_inputs(release, args.limit, args.frame_source, args.split)
    if args.frame_source == "png":
        rows = stage_frames(rows)

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
        "split": args.split,
        "command": cmd,
        "exit_code": exit_code,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "upstream_commit": head,
        "release_sha256": digest,
        "n_sequences": len(rows),
        "metrics_output": metrics,
        "frame_source": args.frame_source,
        "frame_source_detail": (
            "original lossless PNG frames from the RWTH distribution, using the "
            "authors' own released test.txt paths"
            if args.frame_source == "png" else
            "lossy HEVC re-encodings from the shared Volume, not original PNG frames"
        ),
    }
    with open(run_dir + "/run.json", "w") as handle:
        json.dump(meta, handle, indent=2)
    print("=== RUNJSON ===")
    print(json.dumps(meta, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
