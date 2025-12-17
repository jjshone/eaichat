"""Reindex script stub for Qdrant.
This is a starting point: it reads products from the DB and upserts vectors.
Run with: python scripts/reindex_qdrant.py --dry-run
"""
import argparse
import sys


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=128)
    p.add_argument("--collection", type=str, default="products")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    # Placeholder: connect to MySQL, load products, compute embeddings and upsert to Qdrant
    print(f"Reindex stub: collection={args.collection}, batch={args.batch}, dry_run={args.dry_run}")
    if args.dry_run:
        print("Dry run; no changes will be made.")


if __name__ == '__main__':
    main()
