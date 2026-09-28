import argparse
from pathlib import Path

from app.triage.review_log import DEFAULT_REVIEW_LOG, load_reviews, render_review_report

DEFAULT_REPORT = Path("reports/review_learning_report.md")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize triage reviewer feedback.")
    parser.add_argument("--input", type=Path, default=DEFAULT_REVIEW_LOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    reviews = load_reviews(args.input)
    report = render_review_report(reviews, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Wrote review learning report to {args.output}")


if __name__ == "__main__":
    main()
