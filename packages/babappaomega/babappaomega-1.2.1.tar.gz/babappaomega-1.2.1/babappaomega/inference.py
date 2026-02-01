# babappaomega/inference.py
# ============================================================
# BABAPPAΩ — END-TO-END INFERENCE (SCALE-PRESERVING)
# ============================================================

import json
import torch
from collections import Counter

from babappaomega.utils import resolve_device
from babappaomega.tree import load_tree, enumerate_branches
from babappaomega.encoding import encode_alignment
from babappaomega.models import ensure_model


def run_inference(
    alignment_path,
    tree_path,
    out_path,
    device="auto",
    model_tag="frozen",
):
    """
    End-to-end BABAPPAΩ inference entry point (CLI-facing).

    Produces:
    - Backward-compatible probabilistic site scores (sigmoid + averaging)
    - NEW: scale-preserving logit summaries for falsifiable benchmarking

    No retraining required.
    """

    # --------------------------------------------------------
    # DEVICE
    # --------------------------------------------------------
    device = resolve_device(device)

    # --------------------------------------------------------
    # LOAD FROZEN MODEL
    # --------------------------------------------------------
    model_path = ensure_model(model_tag)
    model = torch.jit.load(str(model_path), map_location=device)
    model.eval()

    # --------------------------------------------------------
    # LOAD ALIGNMENT
    # --------------------------------------------------------
    # X: (ntaxa, L) integer-encoded codons
    X, ntaxa, L = encode_alignment(alignment_path)

    if ntaxa < 2:
        raise ValueError(
            "At least two taxa are required for BABAPPAΩ inference. "
            "Single-taxon alignments do not contain branch-specific "
            "evolutionary information."
        )

    # --------------------------------------------------------
    # LOAD TREE
    # --------------------------------------------------------
    tree = load_tree(tree_path)
    branches = enumerate_branches(tree)
    K = len(branches)

    # --------------------------------------------------------
    # MAP BRANCH → DESCENDANT TAXA
    # --------------------------------------------------------
    taxon_names = [leaf.name for leaf in tree.get_leaves()]
    taxon_to_idx = {t: i for i, t in enumerate(taxon_names)}

    branch_to_taxa = []
    for node in tree.traverse("preorder"):
        if node.is_root():
            continue
        desc = [
            taxon_to_idx[leaf.name]
            for leaf in node.get_leaves()
            if leaf.name in taxon_to_idx
        ]
        branch_to_taxa.append(desc)

    # --------------------------------------------------------
    # BUILD BIOLOGICALLY MEANINGFUL INPUTS
    # --------------------------------------------------------
    parent = torch.zeros((1, K, L), dtype=torch.long, device=device)
    child  = torch.zeros((1, K, L), dtype=torch.long, device=device)

    # Global consensus per site
    for i in range(L):
        col = X[:, i].tolist()
        consensus = Counter(col).most_common(1)[0][0]

        for b, taxa in enumerate(branch_to_taxa):
            if not taxa:
                continue
            mismatches = sum(X[t, i] != consensus for t in taxa)
            parent[0, b, i] = len(taxa) - mismatches
            child[0, b, i]  = mismatches

    branch_length = torch.ones((1, K), dtype=torch.float32, device=device)

    # --------------------------------------------------------
    # MODEL FORWARD
    # --------------------------------------------------------
    with torch.no_grad():
        site_logits, branch_logits = model(parent, child, branch_length)

    # --------------------------------------------------------
    # SCALE-PRESERVING AGGREGATES (NEW, CRITICAL)
    # --------------------------------------------------------
    # Raw logits
    site_logits_raw = site_logits.squeeze(0)      # (K, L)
    branch_logits_raw = branch_logits.squeeze(0)  # (K,)

    # Scale-sensitive summaries
    site_logit_mean = site_logits_raw.mean(dim=0)
    site_logit_var  = site_logits_raw.var(dim=0)
    branch_logit_mean = branch_logits_raw

    # Backward-compatible probabilistic outputs
    site_scores = torch.sigmoid(site_logits_raw).mean(dim=0)
    branch_bg   = torch.sigmoid(branch_logits_raw)

    # Move to CPU
    site_scores = site_scores.cpu().numpy().tolist()
    branch_bg   = branch_bg.cpu().numpy().tolist()
    site_logit_mean = site_logit_mean.cpu().numpy().tolist()
    site_logit_var  = site_logit_var.cpu().numpy().tolist()
    branch_logit_mean = branch_logit_mean.cpu().numpy().tolist()

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------
    result = {
        "model": "BABAPPAOmegaBurden",
        "model_tag": model_tag,
        "num_branches": K,
        "num_sites": len(site_scores),

        # Original outputs (unchanged)
        "site_scores": site_scores,
        "branch_background": dict(zip(branches, branch_bg)),

        # NEW: scale-preserving outputs
        "site_logit_mean": site_logit_mean,
        "site_logit_var": site_logit_var,
        "branch_logit_mean": dict(zip(branches, branch_logit_mean)),
    }

    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    return result
