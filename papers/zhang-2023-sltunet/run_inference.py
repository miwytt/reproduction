"""Runs inside the TensorFlow 1.15 container (Python 3.6). Invoked by modal_app.py.

Clones the pinned upstream, unpacks the authors' released artifacts, maps the released
test list onto the sign videos in the shared Volume, runs the authors' published
inference entry point, and scores the output with the repository's own metric code.
"""

from __future__ import print_function

import argparse
import glob
import io
import json
import os
import subprocess
import sys
import time

UPSTREAM = "https://github.com/bzhangGo/sltunet.git"
UPSTREAM_COMMIT = "b1d1d0e8b3b7275e10cd89229f2632b556df5de9"
RELEASE_BASE = "https://data.statmt.org/bzhang/iclr2023_sltunet"
PHOENIX = "/datasets/rwth-phoenix-2014-t"
CSLDAILY = "/datasets/csl-daily"
DGS3T = "/datasets/dgs3-t"
RWTH_ARCHIVE = ("https://www-i6.informatik.rwth-aachen.de/ftp/pub/"
                "rwth-phoenix/2016/phoenix-2014-T.v3.tar.gz")

# One entry per released artifact. The authors published two CSL-Daily archives that differ
# only in the SLTUNET filter_size recorded in sltunet_ckpt/param.json: csldaily is 2048 and
# csldaily2 is 4096. The paper's final configuration (system 15 of Table 2) specifies
# dff=4096, so csldaily2 is the configuration Table 5 reports and csldaily is a
# smaller-FFN variant; both are run so the record shows which one the published row matches
# rather than asserting it. Values other than filter_size are byte-identical between them.
RELEASES = {
    "phoenix": {
        "archive": "phoenix.tar.gz",
        "sha256": "b0e708b7abe5689475905ad11ac578abb02eb0f9bf00b207bbd6d4342afe5152",
        "dataset_root": PHOENIX,
        "bpe_codes": "ende.bpe",
        "gloss_path": "phoenix2014/gloss_dict.npy",
        # infer.sh in the released phoenix archive.
        "eval_batch_size": 4,
        "decode_alpha": 1.0,
        "tokenize": "13a",
        "filter_size": 4096,
    },
    "csldaily": {
        "archive": "csldaily.tar.gz",
        "sha256": "e276481b41e4e6843e3bca78ede16e7387f4f4f2c3893838d4986f3bd1712c8b",
        "dataset_root": CSLDAILY,
        "bpe_codes": "enzh.bpe",
        "gloss_path": "csldaily/gloss_dict.npy",
        # infer.sh in both released csldaily archives uses 2, not phoenix's 4.
        "eval_batch_size": 2,
        "decode_alpha": 1.0,
        "tokenize": "zh",
        "filter_size": 2048,
    },
    "csldaily2": {
        "archive": "csldaily2.tar.gz",
        "sha256": "55e3da80a0e754e8b8797c11f58f83da5779b276703979c29eb71530526f7c1a",
        "dataset_root": CSLDAILY,
        "bpe_codes": "enzh.bpe",
        "gloss_path": "csldaily/gloss_dict.npy",
        "eval_batch_size": 2,
        "decode_alpha": 1.0,
        "tokenize": "zh",
        "filter_size": 4096,
    },
    "dgs3t": {
        "archive": "dgs3-t.tar.gz",
        "sha256": "c5ba62428242e34e47de1b8577d2845c4e7ca9f1d6eb9661c3a738cb9bd34db5",
        "dataset_root": DGS3T,
        "bpe_codes": "ende.bpe",
        "gloss_path": "dgs3-t/gloss_dict.npy",
        "eval_batch_size": 2,
        # The released dgs3-t/infer.sh uses 1.3 here, unlike the other two releases, and
        # unlike the 1.0 recorded in its own param.json. The shell script is the command
        # the authors actually ran, so it wins.
        "decode_alpha": 1.3,
        "tokenize": "13a",
        "filter_size": 4096,
    },
}


def sh(cmd, cwd=None, check=True):
    print("+ " + cmd)
    sys.stdout.flush()
    code = subprocess.call(cmd, shell=True, cwd=cwd)
    if check and code != 0:
        raise RuntimeError("command failed (%d): %s" % (code, cmd))
    return code


def prepare(dataset):
    cfg = RELEASES[dataset]
    src = "/work/sltunet"
    if not os.path.exists(src):
        sh("mkdir -p /work")
        sh("git clone --quiet %s %s" % (UPSTREAM, src))
        sh("git checkout --quiet %s" % UPSTREAM_COMMIT, cwd=src)
    head = subprocess.check_output(
        "git rev-parse HEAD", shell=True, cwd=src
    ).decode().strip()
    assert head == UPSTREAM_COMMIT, "upstream commit mismatch: %s" % head

    tarball = "/results/artifacts/" + cfg["archive"]
    sh("mkdir -p /results/artifacts")
    if not os.path.exists(tarball):
        sh("wget -q -O %s %s/%s" % (tarball, RELEASE_BASE, cfg["archive"]))
    digest = subprocess.check_output(
        "sha256sum %s" % tarball, shell=True
    ).decode().split()[0]
    assert digest == cfg["sha256"], "release sha256 mismatch: %s" % digest

    # Per dataset, so the two CSL-Daily archives never overwrite each other.
    release = "/work/release-" + dataset
    if not os.path.exists(release):
        sh("mkdir -p %s" % release)
        sh("tar xzf %s -C %s" % (tarball, release))

    # The two CSL-Daily archives are distinguished only by this value; assert it so a
    # mislabelled run cannot silently report the other configuration's score.
    with open(release + "/sltunet_ckpt/param.json") as handle:
        got = json.load(handle)["filter_size"]
    assert got == cfg["filter_size"], (
        "%s: expected filter_size %d, released param.json has %d"
        % (dataset, cfg["filter_size"], got))
    return src, release, head, digest


def build_inputs_dgs3t(release, limit, split):
    """Build the DGS3-T decoder inputs from the slices built by build_dgs3t.py.

    The released test.txt names dgs3-t/output/videos/test.<document>.<sentence>.mp4, which
    build_dgs3t.py reproduces exactly: 1575 of 1575 segment names identical, sliced from the
    Public DGS Corpus already on the Volume with the authors' own enumeration and ffmpeg
    parameters. References come from the released sltunet_ckpt/test.bpe.de, so the reference
    text is the authors' own and its tokenization never has to be reconstructed.
    """
    if split != "test":
        raise RuntimeError(
            "DGS3-T dev is not built; only the released test split is supported")

    with open(release + "/test.txt") as handle:
        released = [line.strip() for line in handle if line.strip()]
    with io.open(release + "/sltunet_ckpt/test.bpe.de", encoding="utf-8") as handle:
        refs = [l.rstrip("\n").replace("@@ ", "") for l in handle]
    if len(refs) != len(released):
        raise RuntimeError("released list %d != released references %d"
                           % (len(released), len(refs)))

    rows, missing = [], []
    for path, ref in zip(released, refs):
        name = os.path.basename(path)
        source = "%s/videos/%s" % (DGS3T, name)
        if os.path.exists(source):
            rows.append((name, source, ref))
        else:
            missing.append(name)

    print("frame_source: video (DGS3-T slices built from the Public DGS Corpus)")
    print("released list: %d; mapped: %d" % (len(released), len(rows)))
    if missing:
        print("missing slice (%d): %s" % (len(missing), missing[:5]))
        raise RuntimeError(
            "%d DGS3-T slices are missing; run build_dgs3t.py first" % len(missing))
    if limit:
        rows = rows[:limit]
    return rows


def build_inputs_csldaily(release, limit, split):
    """Build the CSL-Daily decoder inputs, preserving the authors' released test order.

    References come from the released sltunet_ckpt/test.bpe.zh rather than being rebuilt
    from sentence_label/csl2020ct_v2.pkl. That file is the authors' own reference for the
    exact list in test.txt, so hypothesis/reference alignment is guaranteed and no
    reconstruction step can introduce a discrepancy. BPE markers are stripped the same way
    upstream's evalu.eval_metric strips them.

    The released list points at csl-daily/sentence/frames_512x512/<name>/*.jpg. The Volume
    holds the same sequences as MP4, so as on PHOENIX this substitutes the path and lets the
    authors' loader take its non-PNG branch; the pixels are lossy re-encodings.
    """
    if split == "test":
        with open(release + "/test.txt") as handle:
            released = [line.strip() for line in handle if line.strip()]
        names = [l.rsplit("/", 1)[0].rsplit("/", 1)[-1] for l in released]

        with open(release + "/sltunet_ckpt/test.bpe.zh") as handle:
            refs = [l.rstrip("\n").replace("@@ ", "") for l in handle]
        if len(refs) != len(names):
            raise RuntimeError("released list %d != released references %d"
                               % (len(names), len(refs)))
    else:
        # The authors released no dev list or dev reference, so both are rebuilt from the
        # official distribution: split_1.txt for membership and csl2020ct_v2.pkl for the
        # sentences. Joining that file's label_word field with single spaces reproduces the
        # released test reference on 1176 of 1176 lines exactly, so the same reconstruction
        # is used for dev. (label_char does not: it reproduces 1 of 1176, because the
        # released reference is word-segmented.)
        import pickle
        label = CSLDAILY + "/sentence_label"
        with open(label + "/csl2020ct_v2.pkl", "rb") as handle:
            info = pickle.load(handle)["info"]
        by_name = dict((r["name"], r) for r in info)

        names = []
        with open(label + "/split_1.txt") as handle:
            handle.readline()
            for line in handle:
                parts = line.strip().split("|")
                if len(parts) == 2 and parts[1] == split:
                    names.append(parts[0])
        names.sort()
        refs = [" ".join(by_name[n]["label_word"]) for n in names]
        released = names

    rows, missing = [], []
    for name, ref in zip(names, refs):
        source = "%s/videos/%s.mp4" % (CSLDAILY, name)
        if os.path.exists(source):
            rows.append((name, source, ref))
        else:
            missing.append(name)

    print("frame_source: video (CSL-Daily MP4 re-encodings)")
    print("released list: %d; mapped: %d" % (len(released), len(rows)))
    if missing:
        print("missing video (%d): %s" % (len(missing), missing[:5]))
    if limit:
        rows = rows[:limit]
    return rows


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



def run_cascade(src, release, run_dir, list_file, ref_file, rows, cfg):
    """Cascading mode: Sign2Gloss then Gloss2Text, as Table 4's cascading block.

    The paper produces both blocks from one trained model. Pass 1 decodes glosses from
    the sign video and can use --mode infer, which is the image path. Pass 2 translates
    those glosses to text and needs features["source"], which --mode infer cannot supply:
    inference() writes its own source file containing only sign-embedding keys. So pass 2
    goes through --mode test, whose evaluate() takes src_test_file/tgt_test_file.

    evaluate() still opens img_test_file with h5py even when every sample is text-only, so
    a minimal valid h5 is created for it. Every source line carries image index -1, which
    data.to_matrix maps to a zero dummy and an image indicator of 0, so no sign features
    enter pass 2.
    """
    ckpt = release + "/sltunet_ckpt"
    gloss_out = run_dir + "/gloss.txt"

    pass1 = (
        "python run.py --mode infer --parameters="
        "max_len=256,max_img_len=512,eval_batch_size={b},"
        "beam_size=8,remove_bpe=True,decode_alpha={a},gpus=[0],"
        "eval_task='sign2gloss',"
        'src_codes="{c}/{p}",tgt_codes="{c}/{p}",'
        'src_vocab_file="{c}/vocab.zero.drop",tgt_vocab_file="{c}/vocab.zero.drop",'
        'output_dir="{c}",test_output="{g}",img_test_file="{l}",'
        'gloss_path="{r}/{gl}",'
        'sign_cfg="{r}/baseline.yaml",'
        'smkd_model_path="{r}/signemb_ckpt/average.pt",'
    ).format(c=ckpt, g=gloss_out, l=list_file, r=release,
             p=cfg["bpe_codes"], gl=cfg["gloss_path"], b=cfg["eval_batch_size"],
             a=cfg["decode_alpha"])
    rc1 = sh(pass1, cwd=src, check=False)
    if rc1 != 0 or not os.path.exists(gloss_out):
        raise RuntimeError("cascade pass 1 (sign2gloss) failed rc=%d" % rc1)

    with open(gloss_out) as handle:
        glosses = [l.rstrip("\n") for l in handle]
    print("pass 1 produced %d gloss hypotheses for %d inputs" % (len(glosses), len(rows)))
    if len(glosses) != len(rows):
        raise RuntimeError("gloss count %d != input count %d" % (len(glosses), len(rows)))

    # Source for pass 2: image index -1 marks a text-only sample; the tokens are pass 1's
    # gloss hypotheses, left in BPE form because that is the vocabulary the model expects.
    src2 = run_dir + "/cascade.src"
    with open(src2, "w") as handle:
        handle.write("\n".join("-1 " + g.strip() for g in glosses) + "\n")

    dummy_h5 = run_dir + "/dummy.h5"
    import h5py
    import numpy as np
    with h5py.File(dummy_h5, "w") as hf:
        hf.create_dataset("0", data=np.zeros((1, 1024), dtype=np.float32))

    trans2 = run_dir + "/trans.txt"
    pass2 = (
        "python run.py --mode test --parameters="
        "max_len=256,max_img_len=512,eval_batch_size={b},"
        "beam_size=8,remove_bpe=True,decode_alpha={a},gpus=[0],"
        "eval_task='gloss2text',img_feature_size=1024,"
        'src_codes="{c}/{p}",tgt_codes="{c}/{p}",'
        'src_vocab_file="{c}/vocab.zero.drop",tgt_vocab_file="{c}/vocab.zero.drop",'
        'output_dir="{c}",test_output="{t}",'
        'img_test_file="{h}",src_test_file="{s}",tgt_test_file="{f}",'
    ).format(c=ckpt, t=trans2, h=dummy_h5, s=src2, f=ref_file,
             p=cfg["bpe_codes"], b=cfg["eval_batch_size"], a=cfg["decode_alpha"])
    rc2 = sh(pass2, cwd=src, check=False)
    return rc2, trans2


def char_segment(path, out_path):
    """Rewrite one file with every CJK character as its own whitespace-separated token.

    Needed only for CSL-Daily. The authors' released references are word-segmented
    ("他 今年 四 岁 。"), but the paper prints the same number in its tokenized-B@4 and
    sBLEU columns (25.01/25.01 end-to-end, 23.76/23.76 cascading), exactly as it does for
    PHOENIX. sBLEU uses tok.zh, which segments Chinese into characters, so the two columns
    can only coincide if the text scored by the --tokenize none branch was already
    character-segmented. Both segmentations are therefore scored and reported, and the
    published values identify which one the authors used; nothing here is chosen to move a
    score toward the paper.

    Non-CJK runs (digits, Latin, punctuation) are kept whole so that tokens like "2019" are
    not split, matching what tok.zh does.
    """
    def is_cjk(ch):
        return "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿"

    with io.open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    out = []
    for line in lines:
        toks = []
        buf = ""
        for ch in line:
            if ch.isspace():
                if buf:
                    toks.append(buf)
                    buf = ""
            elif is_cjk(ch):
                if buf:
                    toks.append(buf)
                    buf = ""
                toks.append(ch)
            else:
                buf += ch
        if buf:
            toks.append(buf)
        out.append(" ".join(toks))
    with io.open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")
    return out_path


def score(src, run_dir, trans, ref_file, tokenize):
    """Score one run directory with the authors' metric code.

    Table 4 needs both branches of eval/metrics.py. The default (--tokenize 13a) gives the
    SacreBLEU sBLEU and ChrF columns; --tokenize none gives the tokenized B@1-4 and Rouge-L
    columns, which is the "default result" branch upstream and the one the paper's main
    columns use. Scoring twice costs nothing and removes a manual follow-up step.

    Upstream strips BPE inside evalu.eval_metric, but --mode infer writes translations
    through evalu.dump_tanslation, which does not. Reproduce that transformation exactly
    here; it is idempotent, so applying it to already-clean --mode test output is harmless.
    """
    scored = run_dir + "/trans.debpe.txt"
    with open(trans) as handle:
        raw = handle.read()
    with open(scored, "w") as handle:
        handle.write(raw.replace("@@ ", ""))

    proc = subprocess.Popen(
        "python eval/metrics.py -t slt --tokenize %s -hyp %s -ref %s"
        % (tokenize, scored, ref_file),
        shell=True, cwd=src, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    return proc.communicate()[0].decode("utf-8", "replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="full")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--split", default="test", choices=["test", "dev"])
    parser.add_argument("--mode", default="e2e", choices=["e2e", "cascade"])
    parser.add_argument("--frame-source", default="video",
                        choices=["video", "png"])
    # 13a for German (PHOENIX, DGS3-T); zh for Chinese (CSL-Daily), matching the
    # signatures printed in the paper.
    parser.add_argument("--tokenize", default=None,
                        help="defaults to the released artifact's language (13a or zh)")
    parser.add_argument("--dataset", default="phoenix", choices=sorted(RELEASES))
    parser.add_argument("--rescore", action="store_true",
                        help="score an existing run directory without re-running inference")
    args = parser.parse_args()
    cfg = RELEASES[args.dataset]
    if args.tokenize is None:
        args.tokenize = cfg["tokenize"]

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    src, release, head, digest = prepare(args.dataset)
    if args.dataset == "phoenix":
        rows = build_inputs(release, args.limit, args.frame_source, args.split)
        if args.frame_source == "png":
            rows = stage_frames(rows)
    elif args.dataset == "dgs3t":
        rows = build_inputs_dgs3t(release, args.limit, args.split)
    else:
        rows = build_inputs_csldaily(release, args.limit, args.split)

    run_dir = "/results/runs/" + args.tag
    sh("mkdir -p %s" % run_dir)
    list_file = run_dir + "/inputs.txt"
    # Named by target language; the PHOENIX runs already recorded reference.de.
    ref_file = run_dir + ("/reference.zh" if args.dataset.startswith("csldaily")
                          else "/reference.de")
    with open(list_file, "w") as handle:
        handle.write("\n".join(r[1] for r in rows) + "\n")
    with open(ref_file, "w") as handle:
        handle.write("\n".join(r[2] for r in rows) + "\n")

    ckpt = release + "/sltunet_ckpt"
    trans = run_dir + "/trans.txt"
    if args.rescore:
        # Only re-scores what an earlier run already decoded, so the existing trans.txt and
        # reference must both be there; decoding is skipped entirely.
        if not os.path.exists(trans):
            raise RuntimeError("--rescore: no translations at %s" % trans)
        cmd = "rescore-only over existing %s" % trans
        exit_code = 0
    elif args.mode == "cascade":
        cmd = "cascade: run.py --mode infer eval_task=sign2gloss, then run.py --mode test eval_task=gloss2text"
        exit_code, trans = run_cascade(src, release, run_dir, list_file, ref_file,
                                       rows, cfg)
    else:
        # The authors' pinned entry point with their released configuration (infer.sh /
        # param.json); only paths are substituted.
        cmd = (
            "python run.py --mode infer --parameters="
            "max_len=256,max_img_len=512,eval_batch_size={b},"
            "beam_size=8,remove_bpe=True,decode_alpha={a},"
            "gpus=[0],"
            "eval_task='sign2text',"
            'src_codes="{c}/{p}",tgt_codes="{c}/{p}",'
            'src_vocab_file="{c}/vocab.zero.drop",'
            'tgt_vocab_file="{c}/vocab.zero.drop",'
            'output_dir="{c}",'
            'test_output="{t}",'
            'img_test_file="{l}",'
            'gloss_path="{r}/{g}",'
            'sign_cfg="{r}/baseline.yaml",'
            'smkd_model_path="{r}/signemb_ckpt/average.pt",'
        ).format(c=ckpt, t=trans, l=list_file, r=release,
                 p=cfg["bpe_codes"], g=cfg["gloss_path"],
                 b=cfg["eval_batch_size"], a=cfg["decode_alpha"])
        exit_code = sh(cmd, cwd=src, check=False)
    finished = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    metrics = ""
    metrics_tokenized = ""
    metrics_char = ""
    if os.path.exists(trans):
        metrics = score(src, run_dir, trans, ref_file, args.tokenize)
        print("=== METRICS (--tokenize %s) ===" % args.tokenize)
        print(metrics)
        metrics_tokenized = score(src, run_dir, trans, ref_file, "none")
        print("=== METRICS (--tokenize none) ===")
        print(metrics_tokenized)
        if args.dataset.startswith("csldaily"):
            # See char_segment(): which of the two segmentations the paper used is settled
            # by its own published columns, so both are produced.
            hyp_c = char_segment(run_dir + "/trans.debpe.txt",
                                 run_dir + "/trans.char.txt")
            ref_c = char_segment(ref_file, run_dir + "/reference.char.zh")
            proc = subprocess.Popen(
                "python eval/metrics.py -t slt --tokenize none -hyp %s -ref %s"
                % (hyp_c, ref_c),
                shell=True, cwd=src, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            metrics_char = proc.communicate()[0].decode("utf-8", "replace")
            print("=== METRICS (--tokenize none, character-segmented) ===")
            print(metrics_char)

    meta = {
        "tag": args.tag,
        "dataset": args.dataset,
        "release_archive": cfg["archive"],
        "filter_size": cfg["filter_size"],
        "split": args.split,
        "mode": args.mode,
        "command": cmd,
        "exit_code": exit_code,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "upstream_commit": head,
        "release_sha256": digest,
        "n_sequences": len(rows),
        "tokenize": args.tokenize,
        "metrics_output": metrics,
        "metrics_output_tokenize_none": metrics_tokenized,
        "metrics_output_char_segmented": metrics_char,
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
