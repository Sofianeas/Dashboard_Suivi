"""Point d'entrée ETL V1."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from ..ingestion.google_sheets import load_from_xlsx, load_tickets_sheet, load_reference_mappings
from ..transformation.pipeline import transform_tickets
from ..validation.quality import quality_report


def run_xlsx(path: str, output: str) -> dict:
    tickets, clients, problems = load_from_xlsx(path)
    result = transform_tickets(tickets, clients, problems)
    report = quality_report(result)
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False, encoding="utf-8-sig")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def run_google(output: str, credentials: str) -> dict:
    tickets = load_tickets_sheet(credentials_path=credentials)
    clients, problems = load_reference_mappings(credentials_path=credentials)
    result = transform_tickets(tickets, clients, problems)
    report = quality_report(result)
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False, encoding="utf-8-sig")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx")
    parser.add_argument("--google", action="store_true")
    parser.add_argument("--credentials")
    parser.add_argument("--output", default="data/processed/tickets_v1.csv")
    args = parser.parse_args()
    if args.xlsx:
        run_xlsx(args.xlsx, args.output)
    elif args.google:
        if not args.credentials: parser.error("--credentials est requis avec --google")
        run_google(args.output, args.credentials)
    else:
        parser.error("Choisir --xlsx ou --google")
