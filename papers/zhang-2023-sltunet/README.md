# SLTUNET reproduction

**Paper ID:** `zhang-2023-sltunet`

**Citation:** Biao Zhang, Mathias Müller, and Rico Sennrich. SLTUNET: A Simple Unified Model for Sign Language Translation. In The Eleventh International Conference on Learning Representations (ICLR), 2023.

**Paper:** https://openreview.net/forum?id=EBS4C77p_5S · **Code/artifacts:** https://github.com/bzhangGo/sltunet (commit `b1d1d0e8b3b7275e10cd89229f2632b556df5de9`), released weights at https://data.statmt.org/bzhang/iclr2023_sltunet/

**Preference level:** 1

**Pipeline status:** `in_progress` — no terminal pipeline status yet; see "Attempt state" below

**Numerical agreement:** `not_assessed` — no run has been executed, so no value exists to compare

**Attempt date:** 2026-09-13 (opened; not completed)

## Attempt state

This attempt is **open and not ready for review**. It has completed assignment
recording, paper acquisition, target resolution, and source discovery. It has
not built an environment, passed the data gate, run a preflight, trained, or
evaluated anything. Three gates are open and two of them block all execution.

| Stage | State |
| --- | --- |
| Assignment recorded | done |
| Paper acquired and hashed | done |
| Target contract resolved | done — 54 targets |
| Sources discovered and pinned | done for code and paper; released weights not yet downloaded or hashed |
| Environment built | not started |
| Data gate | blocked — gates `modal-auth`, `slt-data-access`, `dgs3t-licence` |
| Preflight | not started |
| Full run | not started |
| Evaluation | not started |

## Reproduction agents

| Agent ID | Model and version | Agent application | Contribution | Attribution evidence / unknowns |
| --- | --- | --- | --- | --- |
| `sonnet-5-claude-code` | Sonnet 5 (`claude-sonnet-5`) | Claude Code | Resolved the assignment URL to the paper identity, acquired and hashed the PDF, discovered and cloned the published code, began the target contract. Executed no experiment. | Interactive Claude Code session on 2026-09-13 declaring this model name and ID. Harness version is not exposed by the session and is recorded as absent. |
| `opus-5-claude-code` | Opus 5 (1M context) (`claude-opus-5[1m]`) | Claude Code | Continued the same session after the session model changed mid-attempt: authored `reproduction.json`, the target ledger, the dataset and licence findings, and the open gates. Executed no experiment. | Same session on 2026-09-13; the environment declared this model name and ID partway through the attempt. Harness version not exposed. |

No run has been executed, so no `runs[].agent_ids` entries exist yet.

## Scope and target contract

The assignment was a bare paper URL (`https://openreview.net/pdf?id=EBS4C77p_5S`)
with no `what_to_reproduce` text and no queue record, so the requested numbers
were resolved from the paper itself rather than from reviewer shorthand.

Scope was set to the **SLTUNET system rows of the three main results tables**,
which carry the paper's headline claims:

- **Table 4** — PHOENIX-2014T, cascading (Sign2Gloss + Gloss2Text) and end-to-end
  (Sign2Text). Dev ROUGE and B@4; test ROUGE, B@1–B@4, and the sBLEU/ChrF pair
  printed in the row bracket.
- **Table 5** — CSL-Daily, same two modes and same metric set.
- **Table 6** — DGS3-T, same two modes, with sBLEU and ChrF in their own columns.

That is 54 targets. Each is one published number with its own `target_id`,
experiment, metric definition, split, and paper location.

Deliberately **out of scope**: the Table 2 optimization ladder (systems 1–15 and
their variants), the Table 3 single-task/multi-task ablation, and the Table 8
shared-versus-separate module ablation. These are analysis ablations supporting
the design, not the paper's reported system results. If the study wants the
ablation ladder reproduced too, the target ledger must be extended.

All 54 targets are the authors' own system, not scores copied from earlier work;
the copied rows in those tables belong to the comparison systems (SL-Transf.,
BN-TIN-Transf.+BT, STMC-Transf., ConSLT, VL-Transfer, PET, STMC-T,
SL-Transformer) and are not targets here.

**Experimental configuration** resolved for every target is system 15 of Table 2,
stated explicitly in section 5.2: `d=256`, `h=4`, `d_ff=4096`, `N^P_enc=1`,
`N^S_enc=5`, `N_dec=6`, CTC regularization `α=0.3`, stochastic BPE dropout with
dropout rate 0.2 and stochastic rate 0.6, Xavier initialization with gain 0.5,
sign-frame random crop and horizontal flip, and the Equation 4 multi-task
objective (Sign2Gloss + Sign2Text + Gloss2Text + MT, excluding Text2Gloss).
Checkpoint rule: average the best 10 checkpoints by dev-set Sign2Text score,
then beam search with beam 8 and a dev-tuned length penalty (Appendix A.1).
Both the cascading and end-to-end numbers in each table come from **one trained
model**, which the paper emphasizes.

**Metric definitions** are pinned in `reproduction.json.metric_definitions`.
B@1–B@4 and ROUGE are tokenized metrics computed by the signjoey-derived scripts
the paper cites; sBLEU and ChrF are SacreBLEU v1.4.2 with the signatures given in
Appendix A.1 (`BLEU+c.mixed+#refs.1+s.exp+tok.{13a,zh}+v.1.4.2` and
`chrF2+c.mixed+#chars.6+#refs.1+space.False+v.1.4.2`). Two protocol notes that
affect comparability were recorded from the paper and the repository:

- On PHOENIX-2014T and CSL-Daily the paper states sBLEU equals B@4, because
  PHOENIX text is pre-tokenized with punctuation removed and CSL-Daily is
  evaluated at character level. The published numbers agree with this, which is
  a useful internal consistency check on any reproduction.
- A repository README update dated 2023-04-02 states that for CSL-Daily the
  authors **always** use subword (not character) preprocessing for target text
  and glosses during training and inference, post-processing to characters only
  at evaluation. This is not stated in the paper and is a genuine protocol
  detail that must be followed.

## Source provenance

| Artifact | Canonical source | Pinned revision / SHA-256 | Role |
| --- | --- | --- | --- |
| Paper PDF | https://arxiv.org/pdf/2305.01778v1 | `51aab83aaed709a042b45ec2bf51faed81ea6f11dd784e4bf2af61326f615add` | Target and protocol source |
| Published code | https://github.com/bzhangGo/sltunet | `b1d1d0e8b3b7275e10cd89229f2632b556df5de9` | Model, training, decoding, metrics, SMKD adaptation, DGS3-T construction |
| Released weights | https://data.statmt.org/bzhang/iclr2023_sltunet/ | not retrieved, not hashed | Intended evaluation-path preflight; unpinned |
| SMKD upstream | https://github.com/ycmin95/VAC_CSLR | not pinned | Cited sign-embedding method; a copy is vendored in the repo under `smkd/` |

**Search performed.** The assignment URL alone did not identify the paper: OpenReview
served an HTTP 403 bot challenge to both the fetch tool and `curl`, and its API
v2 returned a `ChallengeRequiredError`. The paper ID was resolved by web search,
then the camera-ready was obtained from arXiv. The arXiv v1 copy carries the
"Published as a conference paper at ICLR 2023" header and the same tables, and it
is the copy that was hashed; the OpenReview record remains the canonical
citation. The code link came from the paper abstract and was confirmed against
the repository README, which cites the same ICLR paper. The released-weights
directory was found through the repository README update of 2023-07-09 and its
listing confirmed reachable on 2026-09-13.

**Code licence.** The GitHub API reports no licence for `bzhangGo/sltunet` and no
`LICENSE` file exists in the tree at the pinned commit. The code is public but
unlicensed, which permits reading and running it for this reproduction but not
redistribution; no fork or vendored copy will be committed here.

## Results

No target has produced a value. All 54 targets are listed in
`reproduction.json.targets` with their published values and paper locations. The
18 DGS3-T targets already carry a terminal `not_produced` result with reason code
`data_permission_blocked`; the 36 PHOENIX-2014T and CSL-Daily targets have no
result yet because the attempt has not reached execution.

| Target group | Count | Published values | State |
| --- | --- | --- | --- |
| PHOENIX-2014T, cascading (Table 4) | 9 | ROUGE 49.61/49.98, B@4 25.36/26.00, B@1–B@3 50.42/39.24/31.41, sBLEU 26.00, ChrF 51.96 | no result yet |
| PHOENIX-2014T, end-to-end (Table 4) | 9 | ROUGE 52.23/52.11, B@4 27.87/28.47, B@1–B@3 52.92/41.76/33.99, sBLEU 28.47, ChrF 53.78 | no result yet |
| CSL-Daily, cascading (Table 5) | 9 | ROUGE 52.89/53.10, B@4 22.95/23.76, B@1–B@3 54.39/40.28/30.52, sBLEU 23.76, ChrF 21.09 | no result yet |
| CSL-Daily, end-to-end (Table 5) | 9 | ROUGE 53.58/54.08, B@4 23.99/25.01, B@1–B@3 54.98/41.44/31.84, sBLEU 25.01, ChrF 21.99 | no result yet |
| DGS3-T, cascading (Table 6) | 9 | ROUGE 26.40/23.24, B@4 3.49/2.29, B@1–B@3 21.00/8.65/4.25, sBLEU 2.28, ChrF 18.96 | `not_produced` — `data_permission_blocked` |
| DGS3-T, end-to-end (Table 6) | 9 | ROUGE 27.95/24.53, B@4 3.94/2.81, B@1–B@3 23.11/10.05/5.13, sBLEU 2.82, ChrF 20.56 | `not_produced` — `data_permission_blocked` |

(Dev/test pairs are shown as dev/test where both are reported.)

## How to repeat this

No reproduction commands exist yet — no environment has been built. What has
been done so far is source acquisition only:

```bash
# Resolve and hash the paper (OpenReview blocks automated access; arXiv copy used)
curl -sL https://arxiv.org/pdf/2305.01778 -o sltunet.pdf
shasum -a 256 sltunet.pdf   # 51aab83aaed709a042b45ec2bf51faed81ea6f11dd784e4bf2af61326f615add

# Pin the published code
git clone https://github.com/bzhangGo/sltunet.git
git -C sltunet checkout b1d1d0e8b3b7275e10cd89229f2632b556df5de9
```

The published pipeline that a reproduction must execute, taken from
`example/README.md` at the pinned commit, is: (1) download and preprocess
PHOENIX-2014T and MuST-C; (2) pretrain SMKD sign embeddings
(`smkd/preprocess/dataset_preprocess.py`, `smkd/main.py`, `smkd/ckpt_avg.py`,
feature extraction with `--num-feature-aug 10`, then `sign_feature_cmb.py`) to
produce `train/dev/test.h5`; (3) train SLTUNET (`example/train.sh`);
(4) average the top-10 checkpoints (`checkpoint_averaging.py`) and decode
(`example/test.sh`), then score with `eval/metrics.py`.

## Data provenance and permissions

| Dataset | Version/subset/splits | Source and access date | License/permission and cloud-use basis | Path in Volume `datasets` | Counts / manifest / checksum | Deviations |
| --- | --- | --- | --- | --- | --- | --- |
| PHOENIX-2014T | v3; train/dev/test | RWTH Aachen FTP; not accessed | Not yet verified — gate `slt-data-access` | `phoenix-2014t` (not confirmed to exist) | 7,096 / 519 / 642 — paper Table 1, not observed | none yet |
| CSL-Daily | release of Zhou et al. 2021; train/dev/test | USTC page; not accessed | Not verified; distributed under a signed research agreement — gate `slt-data-access` | `csl-daily` (not confirmed to exist) | 18,401 / 1,077 / 1,176 — paper Table 1, not observed | none yet |
| DGS3-T | Public DGS Corpus release 3, authors' document-level split | Not acquired | **Blocked** — licence forbids computational research without express University of Hamburg permission — gate `dgs3t-licence` | `dgs3-t` (not to be populated without permission) | 60,306 / 967 / 1,575 — paper Table 1, not observed | Authors exclude 2 videos with an incorrect 25fps framerate (Appendix A.2) |
| MuST-C En-De | v1.0, text side, 229K | FBK; not accessed | CC BY-NC-ND 4.0, to confirm — gate `slt-data-access` | `must-c-en-de` (not confirmed to exist) | 229K — paper section 5.1, approximate | Punctuation removed from English source and from German for PHOENIX-2014T |
| MuST-C En-Zh | v1.0, text side, 185K | FBK; not accessed | CC BY-NC-ND 4.0, to confirm — gate `slt-data-access` | `must-c-en-zh` (not confirmed to exist) | 185K — paper section 5.1, approximate | Punctuation removed from English source |

**No dataset has been verified.** The Modal CLI is not installed and the
`repro-sign` workspace is not authenticated, so neither the `datasets` Volume nor
the `huggingface-cache` Volume has been listed and
`check_modal_dataset.sh` has not been run for any slug. Every count above is the
paper's published count, not a count observed in data, and no file checksums
exist. The Modal paths are the slugs this attempt intends to use, not paths
confirmed to exist.

**DGS3-T is licence-blocked.** The paper's own data-licensing section states that
the Public DGS Corpus licence "does not allow any computational research except
if express permission is given by the University of Hamburg", and the repository
README repeats it. The authors evidently held such permission; it does not
transfer to this study. The 18 Table 6 targets are therefore terminal
`not_produced` / `data_permission_blocked` pending gate `dgs3t-licence`, which is
routed to Team S.

## Environment and patches

No container has been built and no patch has been written.

The published requirement is **Python 3.8 with TensorFlow 1.15**, stated in the
repository README; there is no `requirements.txt`, `environment.yml`, or lockfile
anywhere in the tree, so exact dependency versions will have to be resolved and
frozen by this attempt. TensorFlow 1.15 needs CUDA 10.0 / cuDNN 7.x, which the
repository's standard GPU base image
(`ghcr.io/sign-language-processing/reproduction:latest`, NVIDIA NGC PyTorch)
does not provide. A paper-specific Dockerfile is therefore expected. That is an
environment adaptation around unmodified published code, not a patch to the
authors' code, but the GPU generation available on Modal may force a real
compatibility decision: TF 1.15 has no kernels for recent architectures, and
`nvidia-tensorflow` or an older NGC TF container may be required. This is
unresolved and untested.

The SLTUNET training path consumes precomputed SMKD sign features from `.h5`
files and does not decode video, so no video decoder is introduced for it. The
SMKD feature-extraction stage does read frames; `simple-video-utils` applies
there if that stage is rerun.

| Patch | Demonstrated failure | Hypothesis | Why necessary | Behavioral effect | Evidence |
| --- | --- | --- | --- | --- | --- |
| none yet | — | — | — | — | — |

## Execution evidence

No run has been executed. `reproduction.json.runs` is empty and no artifacts have
been produced.

| Run ID / agent IDs | Attempt / max | Kind / targets | Platform / hardware | Seed/config | Start/end | Exit / terminal state / reason | Failure class | Stop ceilings | Logs/artifacts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | — | — | — | — | — | — | — | — | — |

## Guesses and deviations

| Detail | Paper/evidence says | This attempt used | Rationale | Effect on interpretation |
| --- | --- | --- | --- | --- |
| Paper copy hashed | Canonical record is OpenReview `EBS4C77p_5S` | arXiv `2305.01778v1` PDF | OpenReview returned HTTP 403 bot challenges to the fetch tool, `curl`, and its own API on 2026-09-13 | The arXiv copy is the ICLR camera-ready and carries the same tables; the two should be re-checked against each other if any target value is ever disputed |
| Target scope | Assignment gave no `what_to_reproduce` | SLTUNET rows of Tables 4, 5, 6 | These carry the paper's reported system results and headline claims; ablation tables support the design rather than reporting the system | If the study wanted the Table 2 ablation ladder, scope must be extended before any run |

No protocol deviation has been made, because nothing has been run.

## Attempts, failures, and dead ends

- **OpenReview PDF fetch (assignment URL).** Hypothesis: the assignment URL
  resolves directly to the paper. Test: fetch tool, then `curl` with a browser
  user agent, then the OpenReview API v2. Result: HTTP 403 with
  `ChallengeRequiredError` in all three cases; the "PDF" saved by `curl` was a
  12 KB HTML error page. Outcome: routed around via web search plus arXiv; no
  credential or bypass attempted. Recorded because it is why the hashed PDF is
  the arXiv copy.
- **Repository licence check.** Hypothesis: the code carries a redistributable
  licence. Test: GitHub API `license` field and a tree-wide `LICENSE` search.
  Result: no licence, either way. Outcome: no fork or vendored copy will be
  committed; the code is pinned by commit and cloned at runtime.

## Candidate flags, ethics, and human evaluation

There is no queue record, so there are no queue comments, copied-score flags,
ethics flags, or compute fields to investigate.

The paper involves no new human evaluation and no participant interaction; all
results are automatic metrics over existing corpora. No ethics gate is opened on
that basis. The DGS3-T restriction is a **licence** matter, not an ethics review,
and is handled at gate `dgs3t-licence` — though note that the Public DGS Corpus
contains identifiable video of 330 named signers, so if permission is granted,
the storage, processing, and reporting terms attached to that permission need to
be read before any data lands on project infrastructure.

## Author and team contact

None. No author has been contacted, and none may be before an independent
attempt. The DGS3-T permission question is routed to Team S as a data-access
matter, not to the paper's authors.
