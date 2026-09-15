# SLTUNET reproduction

**Paper ID:** `3bbc8841012fdb5971d1c86dff528edd8590f1b8` (directory slug
`zhang-2023-sltunet`)

**Citation:** Biao Zhang, Mathias Müller, and Rico Sennrich. SLTUNET: A Simple Unified Model for Sign Language Translation. In The Eleventh International Conference on Learning Representations (ICLR), 2023.

**Paper:** https://openreview.net/forum?id=EBS4C77p_5S · **Code/artifacts:** https://github.com/bzhangGo/sltunet (commit `b1d1d0e8b3b7275e10cd89229f2632b556df5de9`), released weights at https://data.statmt.org/bzhang/iclr2023_sltunet/

**Preference level:** 1

**Pipeline status:** `in_progress` — no terminal pipeline status yet; see "Attempt state" below

**Numerical agreement:** `not_assessed` — no target has produced a value; the
artifact-verification run below is conditional evidence, not a target result

**Attempt date:** 2026-09-13 (opened; not completed)

## Attempt state

This attempt is **open and not ready for review**.

**Pipeline status:** `blocked_on_compute`

**Numerical agreement:** `not_assessed`

Every cell of Tables 4, 5 and 6 that the authors released an artifact for has
now been decoded and scored, on both splits and in both the end-to-end and
cascading modes, and the numbers land very close to the paper. **None of them
produces a target.** They all come from the authors' released checkpoints, not
from training performed here, which under the study's evidence contract is
conditional evidence and cannot close a target however closely it matches. All
54 targets are therefore `not_produced` with reason `compute_budget_blocked`,
gated on `retraining-decision`.

| Stage | State |
| --- | --- |
| Assignment recorded | done |
| Paper acquired and hashed | done |
| Target contract resolved | done — 54 targets |
| Sources discovered and pinned | done — code, paper, and all four released artifacts |
| Modal workspace preflight | done — profile `repro-sign` verified, both canonical Volumes present |
| Data gate | PHOENIX-2014T verified, original frames added; CSL-Daily verified; DGS3-T built and licence cleared; MuST-C absent |
| Environment built | done — TF 1.15 + PyTorch container, five undeclared dependencies pinned |
| Preflight | done — real data, real weights, parsed metrics, exit 0 |
| Table 4 (PHOENIX-2014T) | decoded — end-to-end and cascading, test and dev |
| Table 5 (CSL-Daily) | decoded — end-to-end and cascading, test and dev |
| Table 6 (DGS3-T) | dataset constructed and decoded — end-to-end and cascading, test |
| SMKD pretraining | not started |
| SLTUNET training | not started |

Open gates: `retraining-decision` (the one thing standing between this attempt
and produced targets), `slt-data-access` (MuST-C absent, official channel dead),
`mustc-enzh-version` (En-Zh release unidentified), `smkd-pretraining-scope`
(path decision and cost). Resolved: `modal-auth`, `dgs3t-licence`,
`phoenix-frame-fidelity`, `target-scope-table2`.

Two validator warnings are left standing deliberately rather than papered over.
The queue export carries no `confirmation` field at all and its
`reproduction_status` is `in_progress`, so it does not literally meet the
"confirmed / final" rule; the discrepancy and its status history are recorded in
`assignment.confirmation_status` for a human to judge. The two MuST-C dataset
entries have no split files because the dataset was never obtained; it is needed
only for the MT auxiliary task during training, which is itself gated.

Scope was narrowed by user decision on 2026-09-15 to Tables 4, 5 and 6, dropping
the Table 2 ablations. The queue record asked for "Tables 2, 4, 5 and 6", so this
is a deliberate narrowing: Table 2's claims are deltas between rows, and none of
them is tested by this scope.

## Reproduction agents

| Agent ID | Model and version | Agent application | Contribution | Attribution evidence / unknowns |
| --- | --- | --- | --- | --- |
| `sonnet-5-claude-code` | Sonnet 5 (`claude-sonnet-5`) | Claude Code | Resolved the assignment URL to the paper identity, acquired and hashed the PDF, discovered and cloned the published code, began the target contract. Executed no experiment. | Interactive Claude Code session on 2026-09-13 declaring this model name and ID. Harness version is not exposed by the session and is recorded as absent. |
| `opus-5-claude-code` | Opus 5 (1M context) (`claude-opus-5[1m]`) | Claude Code | Continued the same session after the session model changed mid-attempt: authored `reproduction.json`, the target ledger, the dataset and licence findings, the gates, the container and Modal app, **executed** every run in this attempt (preflight, and the Table 4, 5 and 6 artifact-verification runs across PHOENIX, CSL-Daily and DGS3-T), and **constructed** the DGS3-T sentence-level split. | Same session on 2026-09-13, continued 2026-09-15; the environment declared this model name and ID partway through the attempt. Harness version not exposed. |

Every run so far carries `agent_ids: ["opus-5-claude-code"]`. No run was executed
by `sonnet-5-claude-code`, whose contribution ended before the environment
existed.

## Scope and target contract

> **Scope decided 2026-09-15 — gate `target-scope-table2` resolved.** The attempt
> began from a bare paper URL with no queue record, so scope was resolved from the
> paper. A queue record was later found in this directory and is the authoritative
> assignment; its `what_to_reproduce` is **"Tables 2, 4, 5 and 6"**. The study
> decided to reproduce **without the Table 2 ablations**, so scope is Tables 4, 5
> and 6, the 54 targets below. This is a deliberate narrowing of the requested
> scope and not full coverage: Table 2's claims are all deltas between rows
> ("+1.42 BLEU from CTC", "+5.25 over Baseline"), so **none of them is tested
> here**. Table 2 row 15 is the sole exception, and only incidentally: it is the
> same trained system as the Table 4 rows, so its dev B@4 comes for free.

The original assignment was a bare paper URL
(`https://openreview.net/pdf?id=EBS4C77p_5S`) with no `what_to_reproduce` text and
no queue record, so the requested numbers were resolved from the paper itself.

On that basis scope was set to the **SLTUNET system rows of the three main results
tables**, which carry the paper's headline claims:

- **Table 4** — PHOENIX-2014T, cascading (Sign2Gloss + Gloss2Text) and end-to-end
  (Sign2Text). Dev ROUGE and B@4; test ROUGE, B@1–B@4, and the sBLEU/ChrF pair
  printed in the row bracket.
- **Table 5** — CSL-Daily, same two modes and same metric set.
- **Table 6** — DGS3-T, same two modes, with sBLEU and ChrF in their own columns.

That is 54 targets. Each is one published number with its own `target_id`,
experiment, metric definition, split, and paper location.

Out of scope: the Table 2 optimization ladder (by the study's decision above,
despite the queue record naming it), plus the Table 3 single-task/multi-task
ablation and the Table 8 shared-versus-separate module ablation, which the queue
record does not name.

**Queue record provenance.** `paper_id`
`3bbc8841012fdb5971d1c86dff528edd8590f1b8`, assigned to michelle.wastl@uzh.ch,
paper status `final` (moved from `needs_review` by goehring@cl.uzh.ch on
2026-08-11). Two contract mismatches are recorded rather than papered over: the
export has **no `confirmation` field at all**, and
`ingest_candidate.py` rejects it in its published shape — it is a single JSON
object rather than the required top-level array, and its database `id`
(`cvptk5ysnaqk36e`) differs from its `paper_id`, which the script requires to
match. The record was **not** reshaped to force ingestion, since editing an
assignment record to satisfy a validator would fabricate provenance. It is
preserved verbatim under `reproduction.json.assignment.record`.

**Queue flags investigated.** `copied_scores: "yes"` — in Tables 4–6 the SLTUNET
rows are the authors' own measurements while the comparison rows are quoted from
the cited papers, which the Table 4 caption states outright; all 54 current
targets are the authors' own rows, so none is a copied baseline.
`includes_human_evaluation: "no"` and `potential_ethical_concerns: "no"` are
consistent with the paper, though the latter does not address the Public DGS
Corpus licence or its identifiable signer video. `compute_requirements: "N/A"` is
treated as absent information, not as evidence that compute is small — the paper's
own footnote 3 says the authors could not afford a full grid search.

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
| Released artifacts | https://data.statmt.org/bzhang/iclr2023_sltunet/phoenix.tar.gz | `b0e708b7abe5689475905ad11ac578abb02eb0f9bf00b207bbd6d4342afe5152` | Pretrained SMKD model, trained SLTUNET checkpoint, exact configs, vocab, BPE model |
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

## Artifact verification (conditional evidence, not a target result)

The authors' released checkpoint-averaged SLTUNET model and released SMKD
sign-embedding model were run through their pinned inference entry point over the
full 642-sequence PHOENIX-2014T test split and scored with their own metric code.

| Metric | Published (Table 4, end-to-end, test) | This run | Difference |
| --- | ---: | ---: | ---: |
| B@1 | 52.92 | 52.50 | −0.42 |
| B@2 | 41.76 | 41.33 | −0.43 |
| B@3 | 33.99 | 33.42 | −0.57 |
| B@4 | 28.47 | 27.91 | −0.56 |
| ChrF | 53.78 | 53.43 | −0.35 |

Both SacreBLEU signatures match Appendix A.1 exactly
(`BLEU+case.mixed+numrefs.1+smooth.exp+tok.13a+version.1.4.2` and
`chrF2+case.mixed+numchars.6+numrefs.1+space.False+version.1.4.2`), so the metric
implementation and version are the paper's.

**Independent corroboration.** Output line 2 of the test split is
character-identical to the SLTUNET generation printed in the paper's own Table 10
case study — "am donnerstag in küstennähe regen sonst mal sonne mal wolken im
wechsel dann am freitag ähnliches wetter". Reproducing a published generated
sentence exactly is strong evidence that the decoding configuration, vocabulary,
checkpoint, and input ordering are all correct.

**This does not close any target**, and closeness does not change that:

- No training was performed. These are the authors' own weights, so this verifies
  their released artifact and our evaluation pipeline, not their training pipeline.
- The sign videos are the lossy HEVC re-encodings, not the original frames behind
  the published numbers (gate `phoenix-frame-fidelity`).

**Which eval path this is.** The authors' canonical path is `example/test.sh`
(`run.py --mode test`), which scores internally through `evalu.eval_metric` and
strips BPE from hypotheses and references in a single step. That path consumes
precomputed SMKD features as `test.h5`, which the shared Volume does not hold, so
this attempt used `run.py --mode infer` — the path the authors' own released
`infer.sh` uses to decode from raw video — followed by their `eval/metrics.py`.
Both the decoding and the metric code are the authors'; only the join between them
is ours, which is exactly where the BPE defect arose.

**Reference construction is ruled out as a source of the gap.** Because
`--mode infer` takes no reference, references were built from the PHOENIX
annotation CSV. They were then compared line by line against the authors' own
`sltunet_ckpt/test.bpe.de` from the released tarball, with BPE removed as
`evalu.eval_metric` does: **642 of 642 lines are character-identical**.

**The residual gap is unexplained.** Every metric sits about 0.4–0.6 below the
published value. With the reference eliminated, the leading remaining hypothesis
is the lossy frame source, since the sign encoder consumes raw pixels; hardware
and library nondeterminism is a second, smaller candidate. The discriminating
experiment is to rerun this identical pipeline against the original PNG frames and
compare. No parameter was adjusted to narrow this gap, and none should be.

**A scoring defect was found and fixed along the way.** The first pass scored B@4
22.35. The cause was in this attempt's scoring step: upstream applies BPE removal
only inside `evalu.eval_metric`, while the `--mode infer` path writes output
through `evalu.dump_tanslation` (main.py:538), which does not strip it. Scoring
that raw file counted `@@ ` continuation markers as wrong tokens on 177 of 642
lines (429 markers), costing about 5.5 BLEU. `run_inference.py` now applies
upstream's exact transformation, `line.replace("@@ ", "")`, before scoring. The
authors' code is unmodified.

## Results

**No target has produced a value.** Everything below decodes the authors'
released weights, which verifies their artifacts and this pipeline rather than
reproducing their training. On PHOENIX and CSL-Daily it additionally reads lossy
re-encoded video rather than the frame distributions the released lists name;
the DGS3-T slices are cut from the original corpus videos and do not carry that
second condition. These are behaviour-changing conditions, so by the terminal
contract all of this is conditional evidence regardless of how close the numbers
land.

Across all three tables the published and reproduced values are summarised
below; the full per-cell records, including raw metric output and run IDs, are
in `reproduction.json.conditional_evidence`.

### Exercised: Table 4, end-to-end block (all 9 targets)

| Split | Metric | Published | This attempt | Difference |
| --- | --- | ---: | ---: | ---: |
| dev | ROUGE | 52.23 | 51.88 | −0.35 |
| dev | B@4 | 27.87 | 27.57 | −0.30 |
| test | ROUGE | 52.11 | 51.68 | −0.43 |
| test | B@1 | 52.92 | 52.50 | −0.42 |
| test | B@2 | 41.76 | 41.33 | −0.43 |
| test | B@3 | 33.99 | 33.42 | −0.57 |
| test | B@4 | 28.47 | 27.91 | −0.56 |
| test | sBLEU | 28.47 | 27.91 | −0.56 |
| test | ChrF | 53.78 | 53.43 | −0.35 |

Every value sits **0.30–0.57 below** published. The uniformity is itself
informative: a pipeline defect would produce erratic differences across metrics
and splits, whereas a consistent small offset is what an input-quality or
nondeterminism effect looks like. Reference construction is excluded as a cause —
the constructed references match the authors' own released `test.bpe.de` on
642 of 642 lines.

The dev B@4 also corresponds to **Table 2 row 15** (27.87), because row 15 is this
same trained system. Table 2 is otherwise out of the agreed scope.

### Exercised: Table 4, cascading block (all 9 targets)

The authors publish no cascading entry point, so the two-pass chain was built
from the upstream code paths (see *Guesses and deviations*).

| Split | Metric | Published | This attempt | Difference |
| --- | --- | ---: | ---: | ---: |
| dev | ROUGE | 49.61 | 49.24 | −0.37 |
| dev | B@4 | 25.36 | 24.81 | −0.55 |
| test | ROUGE | 49.98 | 49.64 | −0.34 |
| test | B@1 | 50.42 | 49.03 | −1.39 |
| test | B@2 | 39.24 | 38.28 | −0.96 |
| test | B@3 | 31.41 | 30.61 | −0.80 |
| test | B@4 | 26.00 | 25.26 | −0.74 |
| test | sBLEU | 26.00 | 25.26 | −0.74 |
| test | ChrF | 51.96 | 50.90 | −1.06 |

Wider than the end-to-end block and widest on B@1. Both blocks read the same
lossy frames, but cascading passes that loss through a discrete gloss
bottleneck, where one corrupted gloss removes content the text pass cannot
recover. The constructed two-pass chain is a second candidate explanation the
end-to-end block does not share; the two cannot be separated until the original
PNG frames are used.

### Exercised: Table 5, CSL-Daily (all 18 targets)

| Split | Mode | Metric | Published | This attempt | Difference |
| --- | --- | --- | ---: | ---: | ---: |
| test | end-to-end | ROUGE | 54.08 | 54.35 | +0.27 |
| test | end-to-end | B@1 | 54.98 | 54.76 | −0.22 |
| test | end-to-end | B@2 | 41.44 | 41.28 | −0.16 |
| test | end-to-end | B@3 | 31.84 | 31.72 | −0.12 |
| test | end-to-end | B@4 | 25.01 | 24.94 | −0.07 |
| test | end-to-end | sBLEU | 25.01 | 24.94 | −0.07 |
| test | end-to-end | ChrF | 21.99 | 22.12 | +0.13 |
| dev | end-to-end | ROUGE | 53.58 | 54.22 | +0.64 |
| dev | end-to-end | B@4 | 23.99 | 25.08 | +1.09 |
| test | cascading | ROUGE | 53.10 | 53.58 | +0.48 |
| test | cascading | B@1 | 54.39 | 53.66 | −0.73 |
| test | cascading | B@2 | 40.28 | 40.13 | −0.15 |
| test | cascading | B@3 | 30.52 | 30.55 | +0.03 |
| test | cascading | B@4 | 23.76 | 23.85 | +0.09 |
| test | cascading | sBLEU | 23.76 | 23.85 | +0.09 |
| test | cascading | ChrF | 21.09 | 21.32 | +0.23 |
| dev | cascading | ROUGE | 52.89 | 52.97 | +0.08 |
| dev | cascading | B@4 | 22.95 | 23.28 | +0.33 |

Unlike PHOENIX, differences fall in **both directions**, which is what noise
looks like rather than a systematic input-quality penalty.

Two things had to be resolved here, both from published evidence rather than by
tuning:

**Which released model.** The authors published two CSL-Daily archives and
document no difference. They are identical except `sltunet_ckpt/param.json`
`filter_size`: 2048 in `csldaily.tar.gz`, 4096 in `csldaily2.tar.gz`. The
paper's final configuration specifies dff=4096, so `csldaily2` was expected —
and both were run rather than assumed. `csldaily` (2048) is further from the
published row on every metric (B@4 −0.51, ChrF −0.38, ROUGE −0.72), confirming
the choice. Recorded in `reproduction.json.artifact_selection`.

**How Chinese is scored.** The paper prints the same number in its B@4 and sBLEU
columns (25.01/25.01), which is only possible if the tokenized branch saw
character-segmented text, since sBLEU uses `tok.zh`. Both segmentations were
computed. Character-segmenting and scoring with `--tokenize none` reproduces
SacreBLEU's own `tok.zh` BLEU to three decimals (54.761 vs 54.762) and lifts
ROUGE from 49.54 to 54.35 against a published 54.08; word segmentation is off by
4.5 ROUGE. So the paper's CSL-Daily columns are character-level, and no
self-implemented BLEU was needed after all.

The dev rows carry an extra caveat: the authors released no CSL-Daily dev list
or reference, so both are rebuilt from the official distribution (`split_1.txt`,
`csl2020ct_v2.pkl`). That reconstruction reproduces the released *test*
reference on 1176 of 1176 lines exactly, which is what licenses using it for
dev — but the dev ordering is this attempt's choice. dev B@4 at +1.09 is the
largest gap in the table.

### Exercised: Table 6, DGS3-T test (14 of 18 targets)

DGS3-T is not distributable; it is a sentence-level slicing of the Public DGS
Corpus that had to be **constructed** (see *Data provenance*).

| Mode | Metric | Published | This attempt | Difference |
| --- | --- | ---: | ---: | ---: |
| end-to-end | ROUGE | 24.53 | 24.64 | +0.11 |
| end-to-end | B@1 | 23.11 | 23.14 | +0.03 |
| end-to-end | B@2 | 10.05 | 10.15 | +0.10 |
| end-to-end | B@3 | 5.13 | 5.23 | +0.10 |
| end-to-end | B@4 | 2.81 | 2.94 | +0.13 |
| end-to-end | sBLEU | 2.82 | 2.92 | +0.10 |
| end-to-end | ChrF | 20.56 | 20.52 | −0.04 |
| cascading | ROUGE | 23.24 | 23.25 | +0.01 |
| cascading | B@1 | 21.00 | 19.30 | −1.70 |
| cascading | B@2 | 8.65 | 8.15 | −0.50 |
| cascading | B@3 | 4.25 | 4.05 | −0.20 |
| cascading | B@4 | 2.29 | 2.19 | −0.10 |
| cascading | sBLEU | 2.28 | 2.18 | −0.10 |
| cascading | ChrF | 18.96 | 18.29 | −0.67 |

The end-to-end block is the **closest agreement in this attempt** — every metric
within 0.15. That is consistent with these slices being cut from the same source
videos the authors sliced, rather than from a re-encoding as on PHOENIX. The
cascading block again shows the B@1-heavy shortfall seen on PHOENIX.

**The four DGS3-T dev targets are not exercised.** The authors released a test
list and test reference but neither for dev. Dev sentences can be enumerated the
same way, but their German is raw ELAN text while the authors' reference is
Moses-tokenized and escaped; scoring untokenized references against a model that
emits tokenized text would depress the score for reasons unrelated to the
reproduction. Recorded in `open_questions`.

Published values for every target are in `reproduction.json.targets`.

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

Verified 2026-09-13 through `modal_repro_sign.sh` under profile `repro-sign`.
Both canonical Volumes (`datasets`, `huggingface-cache`) exist.

| Dataset | Version/subset/splits | Source and access date | License/permission and cloud-use basis | Path in Volume `datasets` | Counts / manifest / checksum | Deviations |
| --- | --- | --- | --- | --- | --- | --- |
| PHOENIX-2014T | v3; train/dev/test | Already in shared Volume; verified 2026-09-13 | Held by the study, not by this attempt — confirm at gate `slt-data-access`. Mounted read-only | `rwth-phoenix-2014-t` ✅ | **7,096 / 519 / 642 — observed, exact match to Table 1**; per-split CSV checksums in `reproduction.json` | none |
| CSL-Daily | csl2020ct_v2 + split_1.txt | Already in shared Volume; verified 2026-09-13 | Held by the study — confirm at gate `slt-data-access`. Mounted read-only | `csl-daily` ✅ | **18,401 / 1,077 / 1,176 — observed, exact match to Table 1**; `split_1.txt` sha256 `45960c86…` | Subword (not char) preprocessing per repo README update |
| DGS3-T | Public DGS Corpus 3.0.0, UZH document split | Present in shared Volume; split manifest read 2026-09-13 | **Permission unresolved** — licence forbids computational research without express University of Hamburg permission — gate `dgs3t-licence` | `dgs-corpus` (present, not to be processed) | Manifest declares 384 / 10 / 10 **documents**, matching Appendix A.2; sha256 `a6876220…` | Authors exclude 2 videos with an incorrect 25fps framerate (Appendix A.2) |
| MuST-C En-De | v1.0, text side, 229K | **Absent** | CC BY-NC-ND 4.0, FBK registration — gate `slt-data-access` | not present ❌ | 229K — paper section 5.1, approximate | Punctuation removed from English source and from German for PHOENIX-2014T |
| MuST-C En-Zh | v1.0, text side, 185K | **Absent** | CC BY-NC-ND 4.0, FBK registration — gate `slt-data-access` | not present ❌ | 185K — paper section 5.1, approximate | Punctuation removed from English source |

**PHOENIX-2014T and CSL-Daily are verified.** `check_modal_dataset.sh` confirmed
both slugs, and sentence counts parsed from the actual annotation manifests match
paper Table 1 exactly. Note the volume slug is `rwth-phoenix-2014-t`, not the
`phoenix-2014t` this attempt initially assumed.

**MuST-C is missing, is not optional, and has no working official source.** The
Equation 4 objective includes the MT task for every reported SLTUNET result, so
no target can be reproduced without it. As of 2026-09-13 the corpus has no live
distribution channel: `mustc.fbk.eu` returns NXDOMAIN, the
`ict.fbk.eu/must-c` URL cited by the published repository 301-redirects to a
generic FBK page, and MuST-C is no longer listed at `mt.fbk.eu/resources/`.
Third-party Hugging Face mirrors exist for German and a few other languages but
carry licence tags (`afl-3.0`, `apache-2.0`) that contradict the corpus's stated
CC BY-NC-ND 4.0 and are CSV conversions rather than the original release, so
neither their identity nor their licence basis can be established. Acquisition is
a decision for Team S, not a download — see gate `slt-data-access`.

**The En-Zh release is unidentified, and v1.0 cannot be the answer.** The paper
cites Di Gangi et al. (2019) for both MT sets and reports 185K En-Zh samples, but
that paper's abstract, section 1, and Table 2 all state MuST-C covers English into
eight languages — Dutch, French, German, Italian, Portuguese, Romanian, Russian,
Spanish — with **no Chinese portion**. The FBK release history, recovered from the
Internet Archive, confirms Chinese first appears in v1.2:

| Release | Coverage |
| --- | --- |
| v1.0 | 8 directions (En→Nl, Fr, De, It, Pt, Ro, Ru, Es) — **no Chinese** |
| v1.1 | IWSLT-2019 special release, +En-Cs, text only |
| v1.2 | 14 directions — **first release with Chinese** |
| v2.0 | En→{German, Chinese, Japanese} |
| v3.0 | En→German only |

So the En-Zh data came from v1.2 or v2.0, and nothing states which. The repository
pins v1.0 for En-De only. Picking a release silently would be an invented protocol
detail affecting all 18 CSL-Daily targets, so this is gated at
`mustc-enzh-version`; any CSL-Daily run made on a guess is conditional evidence,
not a produced target. This gate does **not** block the PHOENIX-2014T targets.

**Identity fingerprints for verifying any candidate copy.** Di Gangi et al. (2019)
Table 2 gives En-De as 2,093 talks / 234K sentences, consistent with the 229K
training samples reported here after the dev (1.4K) and test (2.5K) holdouts. For
En-Zh there is no such fingerprint, since that paper has no Chinese section; the
only check is whether the v1.2 or v2.0 Chinese portion contains ~185K segments,
which is also how the version question should be settled.

**The PHOENIX features in the Volume are the wrong ones.** `features/phoenix14t.pami0.*`
are the Camgoz et al. (2020b) embeddings — the paper's Table 2 row 1.1, scoring
21.21 B@4 on dev. The targets require the authors' retrained SMKD embeddings with
a 2D ResNet34 backbone, so these cannot be substituted.

**But the authors released the SMKD model itself.** `phoenix.tar.gz` (1,014,073,705
bytes, sha256 `b0e708b7…`, gzip integrity verified 2026-09-13) contains far more
than weights:

| File | Size | What it is |
| --- | ---: | --- |
| `signemb_ckpt/average.pt` | 519 MB | The pretrained SMKD sign-embedding model |
| `sltunet_ckpt/average-0.*` | 589 MB | The checkpoint-averaged trained SLTUNET model |
| `sltunet_ckpt/param.json` | — | Exact runtime hyperparameters |
| `sltunet_ckpt/vocab.zero.drop`, `ende.bpe` | — | Joint vocabulary and BPE model |
| `infer.sh`, `signemb.sh`, `sltunet.sh`, `baseline.yaml`, `configs/phoenix14.yaml` | — | Exact run configuration |

`param.json` independently corroborates the target configuration read from the
paper: `hidden_size 256`, `num_heads 4`, `filter_size 4096`, `num_encoder_layer 6`
(= `N^P_enc=1` + `N^S_enc=5`), `num_decoder_layer 6`, `beam_size 8`,
`decode_alpha 1.0` — matching system 15 of Table 2 and Appendix A.1.

This opens **three paths that answer different questions**, tracked at gate
`smkd-pretraining-scope`:

1. **Inference only** from the released SLTUNET checkpoint — verifies the authors'
   artifact and our evaluation pipeline, reproduces no training. Needs no MuST-C
   and no SMKD pretraining, so it is unblocked today.
2. **SLTUNET training** from the released SMKD embeddings — reproduces the paper's
   own training but inherits their sign encoder. Still needs MuST-C.
3. **Full reproduction** including SMKD pretraining from video — the only path that
   reproduces the whole pipeline. Needs MuST-C and is the expensive one.

Path 1 is the recommended first step regardless of which the study ultimately
wants, because it validates the TensorFlow 1.15 container, the decoding settings,
and the metric implementation against published numbers before anything expensive
runs. Whichever path is chosen, reused artifacts are recorded as such: a score
obtained from the authors' own weights is **artifact verification, not a
reproduction of their training**, and cannot close a target as if it were.

**DGS3-T: availability is no longer the obstacle, permission is.** The shared
Volume already contains `dgs-corpus/` including `split.3.0.0-uzh-document.json`,
which *is* the DGS3-T protocol: version 3.0.0, 384/10/10 documents, matching
Appendix A.2's "desired number of documents in the development and test set is
10", and tagged `uzh` for the authors' own institution. Only that manifest was
read, to establish gate status; no corpus content was processed. The Public DGS
Corpus licence still forbids computational research without express University of
Hamburg permission, and this attempt has no record of whether the study holds it
or what it covers. Treating presence as permission would be working around a
restriction, so the 18 Table 6 targets stay terminal `not_produced` /
`data_permission_blocked` pending gate `dgs3t-licence`.

## Environment and patches

**No patch to the authors' code has been needed.** The reproduction stays at
preference level 1: the pinned upstream entry point is invoked directly with the
authors' own released configuration, and only paths are substituted.

**The container must carry two frameworks in one process.** `main.py inference()`
imports `smkd.sign_embedder.SignEmbedding`, which is PyTorch, and feeds its output
into the TensorFlow graph — so TF 1.15 and PyTorch must coexist. The image is the
public `tensorflow/tensorflow:1.15.5-gpu-py3` plus `torch==1.7.1+cu101`,
`torchvision==0.8.2+cu101`, and `opencv-python-headless==4.6.0.66`. The NGC `tf1`
images would allow newer GPUs, but `nvcr.io` returned HTTP 401 for anonymous
manifest requests and obtaining registry credentials is a secrets gate, so they
were not pursued. Because the image is CUDA 10, the GPU must be Turing or older;
runs use **T4**. The repository's standard GPU base image is deliberately not used
— it supplies NGC PyTorch, not TensorFlow 1.15.

**Frame source is a real fidelity caveat** (gate `phoenix-frame-fidelity`). The
authors' released `test.txt` points at
`features/fullFrame-210x260px/test/SEQNAME/*.png` — lossless frames, which is what
their published numbers came from. The shared Volume instead holds
`videos/test/SEQNAME.mp4`, **HEVC-encoded, muxed with Lavf 61.7.100**, i.e. a recent
lossy re-encode made by the study; one test sequence is 34 KB. SMKD consumes raw
pixels, so compression artifacts can shift features and therefore scores by an
unmeasured amount. No code change is needed to read either form — the authors'
own loader (`smkd/dataset/dataloader_video.py`, lines 65–77) branches on the path
suffix and opens non-PNG paths with `cv2.VideoCapture` — so this is a path
substitution, not a patch. The original 41.7 GB distribution is still live at
RWTH if the study wants the faithful comparison.

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

| Run ID / agent IDs | Attempt / max | Kind / targets | Platform / hardware | Config | Start/end (UTC) | Exit / terminal / reason | Failure class | Stop ceilings | Outputs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `artifact-verification-phoenix-sign2text-attempt-1` / `opus-5-claude-code` | 1 / 2 | evaluation-only; no target | Modal `repro-sign`, Sandbox, 1×T4, 8 CPU, 32 GB | beam 8, `decode_alpha` 1.0, `eval_batch_size` 4, `max_img_len` 512 | 11:39:44 → 11:43:53 (249 s) | 0 / `succeeded` / `completed` | none | 6 h wall, 6 GPU-h, CHF 10 | Volume `zhang-2023-sltunet-results`, `runs/artifact-verification-full/` |

Modal app `ap-NdzBowjcaHYf2cX2VcPEIy`, profile `repro-sign`, executed as a Sandbox
(not a Function — see Environment). Upstream commit
`b1d1d0e8b3b7275e10cd89229f2632b556df5de9`, released artifact sha256
`b0e708b7abe5689475905ad11ac578abb02eb0f9bf00b207bbd6d4342afe5152`, base image
`tensorflow/tensorflow:1.15.5-gpu-py3`. Raw outputs (`trans.txt`,
`trans.debpe.txt`, `reference.de`, `inputs.txt`, `run.json`) are retained on that
Volume rather than in Git.

An earlier pass in the same attempt group scored B@4 22.35 and is not retained as
a separate run, because it measured this attempt's own scoring defect rather than
the reproduction. The defect, its magnitude and its fix are recorded above and in
`reproduction.json`.

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
- **Dataset gate, 2026-09-13.** Hypothesis: the three SLT corpora are absent from
  the shared Volume and must be acquired. Test: wrapper volume listing plus
  `check_modal_dataset.sh` per slug, then parsing the annotation manifests.
  Result: hypothesis wrong on all three counts — PHOENIX-2014T and CSL-Daily are
  present with counts matching Table 1 exactly, and the DGS corpus with the
  authors' own UZH split is present too. MuST-C is the one that is genuinely
  absent. Outcome: `slt-data-access` narrowed to MuST-C plus a licence-basis
  confirmation; `dgs3t-licence` reframed from an availability question to a
  permission question.
- **MuST-C acquisition hunt, 2026-09-13.** Hypothesis: the MuST-C paper or the
  Internet Archive would expose a working download. Test: DNS and HTTP probes of
  the FBK hosts, Wayback CDX enumeration, and retrieval of the last HTTP 200
  snapshot of the download page (2023-05-28). Result: no download was ever
  archived — even that snapshot reads "(available soon...)" in the "How to obtain
  MuST-C" section, and its only external links were two Google Drive READMEs now
  returning 404. Outcome: hypothesis rejected; MuST-C stays a Team S request. The
  attempt was not wasted — the same snapshot yielded the release history that
  rules out v1.0 for Chinese, and the MuST-C paper yielded the En-De identity
  fingerprint (2,093 talks / 234K sentences) for checking any future copy.
- **Pivot to the authors' released artifacts.** Hypothesis: the released archives
  are weights only and cannot substitute for missing data. Test: fetched
  `phoenix.tar.gz` and listed it. Result: hypothesis wrong — it ships the
  pretrained SMKD model, the trained checkpoint-averaged SLTUNET model, and the
  exact configs, which both corroborates the target configuration and opens an
  inference-only path that no open data gate blocks. Note the server ignored the
  HTTP range request, so the full 1 GB was fetched rather than a header slice.
- **Sign-feature provenance check.** Hypothesis: the precomputed
  `features/phoenix14t.pami0.*` in the Volume could shortcut SMKD pretraining.
  Test: matched them against the paper's ablation ladder. Result: they are the
  Camgoz et al. (2020b) embeddings, which Table 2 row 1.1 scores at 21.21 B@4;
  the targets need the retrained SMKD ResNet34 embeddings from row 15. Outcome:
  shortcut rejected as a behaviour-changing deviation that would reproduce a
  different row; SMKD pretraining from video stays in scope and is gated for
  cost at `smkd-pretraining-scope`.

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
