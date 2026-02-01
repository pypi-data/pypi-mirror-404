# babappaomega/cli.py

import argparse
from babappaomega.inference import run_inference
from babappaomega.interpret import interpret_results


def main():
    parser = argparse.ArgumentParser(
        prog="babappaomega",
        description=(
            "BABAPPAΩ: likelihood-free inference of episodic "
            "selection burden in phylogenetic data"
        )
    )

    parser.add_argument("--alignment", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True,
                        help="Output JSON file")
    parser.add_argument("--device", default="auto",
                        choices=["auto", "cpu", "cuda"])
    parser.add_argument("--model", default="frozen")

    parser.add_argument(
        "--no-interpretation",
        action="store_true",
        help="Disable generation of human-readable interpretation"
    )

    args = parser.parse_args()

    # ------------------------------------------------
    # RUN INFERENCE (JSON)
    # ------------------------------------------------
    results = run_inference(
        alignment_path=args.alignment,
        tree_path=args.tree,
        out_path=args.out,
        device=args.device,
        model_tag=args.model,
    )

    # ------------------------------------------------
    # RUN INTERPRETATION (TXT)
    # ------------------------------------------------
    if not args.no_interpretation:
        txt_out = args.out.replace(".json", ".interpretation.txt")
        report = interpret_results(results)

        with open(txt_out, "w") as f:
            f.write(report)

        print(f"[OK] Interpretation written to {txt_out}")


if __name__ == "__main__":
    main()
