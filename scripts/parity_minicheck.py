"""Parity check: learnmate.verify.MiniCheckFT5 vs official MiniCheck package (pinned commit b58b9fa)."""
import numpy as np
from learnmate.verify import MiniCheckFT5
from learnmate.io_utils import write_json

docs = [
    "Dropout breaks up co-adaptation by zeroing out hidden units at random during training, which acts as a regularizer.",
    "The forget gate determines whether to keep the current value of the memory or flush it.",
    "AlexNet used dropout in its fully connected layers and data augmentation to control capacity.",
    "Adagrad divides the learning rate by the square root of accumulated squared gradients.",
]
claims = [
    "Dropout acts as a regularizer by randomly zeroing hidden units during training.",
    "The forget gate decides whether to keep or flush the memory.",
    "Dropout forces the network to learn more robust and generalized features.",
    "Adagrad multiplies the learning rate by the accumulated squared gradients.",
]
ours = MiniCheckFT5(revision="96eafd01cee2d16cf81aaa2fb226b14f422a37b3").score_pairs(docs, claims)
import re
import minicheck.inference as _mi
# NLTK punkt data cannot be fetched through this environment's proxy (NLTK SSRF policy); all docs here are
# far below the 500-word chunk size, so sentence splitting cannot change the official result.
_mi.sent_tokenize = lambda t: [x for x in re.split(r"(?<=[.!?])\s+", t) if x]
from minicheck.minicheck import MiniCheck
_, off, _, _ = MiniCheck(model_name="flan-t5-large").score(docs=docs, claims=claims)
off = np.array(off)
print("ours    ", np.round(ours, 4)); print("official", np.round(off, 4))
diff = float(np.abs(ours - off).max()); print("max abs diff", diff)
write_json("results/smoke/minicheck_parity.json", {"ours": ours.tolist(), "official": off.tolist(), "max_abs_diff": diff,
           "official_commit": "b58b9fa69acbd1015ec970fa65dd752413a053d2"})
assert diff < 1e-3, diff
