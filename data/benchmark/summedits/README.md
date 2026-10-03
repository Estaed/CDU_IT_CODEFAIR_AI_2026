# SummEdits sample for the checker evaluation

`sample.jsonl` holds 300 (document, summary, label) pairs from SummEdits, used to measure Jev
against Claude-as-checker (Task-08, `uv run python -m readmark eval --part checker --replay`).

## Source

- **Release:** Hugging Face dataset `Salesforce/summedits`, file `summedits.json` (6,348 pairs,
  10 domains), revision `ce0c479aaf59259abb6b67e42248b2f49004b7d5`:
  <https://huggingface.co/datasets/Salesforce/summedits>. Download URL pinned in
  `readmark/eval/summedits.py`; SHA-256 of the file
  `21e34593330020d02b7d92f4651fdcc550f7d79a2f899392f106fd816c215a89`, checked before sampling.
- **Code and paper repo:** <https://github.com/salesforce/factualNLG> (the same per-domain files
  under `data/summedits/`; the repo's code licence is Apache-2.0).
- **Licence:** CC BY 4.0, as stated on the dataset card (`license: cc-by-4.0`), checked
  2026-10-03. The pairs here are copied unchanged apart from the fields listed below.
- **Caveat on upstream documents:** SummEdits builds its documents from earlier corpora, and some
  carry their own terms. The SAMSum dialogues (domain `samsum`, 30 pairs here) come from a corpus
  distributed under CC BY-NC-ND 4.0 according to its dataset card. Our use is non-commercial,
  academic and attributed; anyone reusing this sample commercially should check each domain's
  upstream terms.

## Citation

Philippe Laban, Wojciech Kryscinski, Divyansh Agarwal, Alexander Fabbri, Caiming Xiong, Shafiq
Joty and Chien-Sheng Wu. 2023. *SummEdits: Measuring LLM Ability at Factual Reasoning Through The
Lens of Summarization.* In Proceedings of the 2023 Conference on Empirical Methods in Natural
Language Processing (EMNLP), pages 9662–9676, Singapore. ACL.
<https://aclanthology.org/2023.emnlp-main.600/>, doi:10.18653/v1/2023.emnlp-main.600.

## How it was sampled

`uv run python -m readmark.eval.summedits <summedits.json>` (seed 20261003):

- stratified by domain and label: 15 consistent (label 1) and 15 inconsistent (label 0) pairs from
  each of the 10 domains, drawn with one seeded generator in a fixed order (domain, then label;
  candidates sorted by release id), so n = 300, 150 per label, 30 per domain;
- then shuffled with the same generator and renumbered `s001`–`s300`. The release ids stay in
  `source_id` but are never sent to a model: they end in `_og` for unedited seed summaries, which
  would leak the label;
- a document over 15,000 words would be skipped with a count rather than truncated (Jev's context
  is 32K tokens). None is: the longest document in the sample is 2,090 words, so 0 were skipped.

The sample covers 160 distinct documents; several summaries (edits) share a document.

## Fields

`sample_id`, `source_id` (release `id`), `domain`, `label` (1 consistent, 0 inconsistent),
`edit_types` (the release's GPT-4 classification of the edit, for inconsistent pairs), `doc`,
`summary`. The release's `seed_summary` is not copied.
