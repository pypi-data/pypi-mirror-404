# babappaomega/interpret.py
# ============================================================
# BABAPPAΩ — BIOLOGICAL INTERPRETATION LAYER
# ============================================================

import numpy as np
import re


def _zscore(x):
    mu = np.mean(x)
    sd = np.std(x) + 1e-12
    return (x - mu) / sd


def _is_terminal_branch(name):
    """
    Exclude internal / bootstrap-like nodes.
    """
    if re.fullmatch(r"[0-9.]+/[0-9.]+", name):
        return False
    if "_" not in name:
        return False
    if not re.search(r"[A-Za-z]", name):
        return False
    return True


def interpret_results(
    results,
    top_sites=20,
    top_branches=10,
    branch_sites=10,
):
    """
    Convert BABAPPAΩ JSON output (dict) into a human-readable report string.
    """

    site_scores = np.array(results["site_scores"])
    all_branches = list(results["branch_background"].keys())
    all_branch_bg = np.array(list(results["branch_background"].values()))

    # --------------------------------------------
    # FILTER TERMINAL BRANCHES
    # --------------------------------------------
    branches = []
    branch_bg = []

    for b, v in zip(all_branches, all_branch_bg):
        if _is_terminal_branch(b):
            branches.append(b)
            branch_bg.append(v)

    branch_bg = np.array(branch_bg)

    site_z = _zscore(site_scores)
    branch_z = _zscore(branch_bg)

    top_sites_idx = np.argsort(site_z)[::-1][:top_sites]
    top_branches_idx = np.argsort(branch_z)[::-1][:top_branches]

    lines = []
    lines.append("BABAPPAΩ — INTERPRETED RESULTS")
    lines.append("=" * 60)
    lines.append("")

    # ------------------------------------------------
    # SUMMARY
    # ------------------------------------------------
    lines.append("1. SUMMARY")
    lines.append("-" * 60)
    lines.append(
        f"This analysis evaluated {len(site_scores)} codon sites "
        f"across {len(branches)} terminal evolutionary branches.\n"
    )

    lines.append(
        "Scores represent episodic selection burden:\n"
        "- Higher values indicate lineage-specific evolutionary stress\n"
        "- Interpretation is relative, not absolute\n"
    )

    # ------------------------------------------------
    # BRANCH RANKING
    # ------------------------------------------------
    lines.append("2. TERMINAL BRANCHES WITH STRONGEST GLOBAL DEVIATION")
    lines.append("-" * 60)

    for rank, idx in enumerate(top_branches_idx, start=1):
        lines.append(
            f"{rank:2d}. {branches[idx]:40s}  "
            f"background={branch_bg[idx]:.4f}  "
            f"z={branch_z[idx]:+.2f}"
        )

    lines.append(
        "\nInterpretation:\n"
        "Branches listed above show unusually high overall evolutionary\n"
        "stress at this gene compared to other terminal lineages.\n"
    )

    # ------------------------------------------------
    # SITE RANKING
    # ------------------------------------------------
    lines.append("3. SITES WITH STRONGEST EPISODIC SELECTION BURDEN")
    lines.append("-" * 60)

    for rank, i in enumerate(top_sites_idx, start=1):
        lines.append(
            f"{rank:2d}. Site {i+1:4d}  "
            f"score={site_scores[i]:.4f}  "
            f"z={site_z[i]:+.2f}"
        )

    lines.append(
        "\nInterpretation:\n"
        "These codon positions show unusually high episodic deviation,\n"
        "likely driven by a subset of branches rather than uniform\n"
        "divergence across the tree.\n"
    )

    # ------------------------------------------------
    # PER-BRANCH SITE HOTSPOTS
    # ------------------------------------------------
    lines.append("4. PER-BRANCH PUTATIVE EPISODIC DRIVER SITES")
    lines.append("-" * 60)

    for idx in top_branches_idx:
        bname = branches[idx]
        lines.append(f"\nBranch: {bname}")
        lines.append("-" * (8 + len(bname)))

        for i in top_sites_idx[:branch_sites]:
            lines.append(
                f"  - Site {i+1:4d}  "
                f"score={site_scores[i]:.4f}  "
                f"z={site_z[i]:+.2f}"
            )

        lines.append(
            "  Interpretation:\n"
            "  These sites are putative contributors to the elevated\n"
            "  evolutionary stress observed on this branch.\n"
        )

    # ------------------------------------------------
    # FINAL NOTES
    # ------------------------------------------------
    lines.append("5. INTERPRETATION NOTES")
    lines.append("-" * 60)
    lines.append(
        "- Internal tree nodes are excluded from reporting.\n"
        "- Scores are not dN/dS or ω estimates.\n"
        "- Values reflect relative evolutionary stress.\n"
        "- Per-branch site lists indicate putative drivers, not\n"
        "  definitive causal substitutions.\n"
        "- High-ranking sites should be mapped to protein domains\n"
        "  or structural models for validation.\n"
    )

    return "\n".join(lines)
