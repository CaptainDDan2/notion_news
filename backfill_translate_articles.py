#!/usr/bin/env python3
"""
Backfill translation for stored articles.
"""

import argparse
import sys
from datetime import datetime

from database import get_db_session, NewsArticle
from news_analyzer import NewsAnalyzer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill Korean translations for stored articles.")
    parser.add_argument("--limit", type=int, default=0, help="Max number of articles to process (0 = no limit).")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing.")
    parser.add_argument("--update-summary", action="store_true", help="Regenerate summary when content changes.")
    parser.add_argument("--include-title", action="store_true", help="Translate English titles in DB.")
    parser.add_argument("--include-content", action="store_true", help="Translate English content in DB.")
    parser.add_argument("--allow-no-api", action="store_true", help="Run even if OPENAI_API_KEY is missing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.include_title and not args.include_content:
        print("Nothing to do. Use --include-title and/or --include-content.")
        return 1

    analyzer = NewsAnalyzer()
    if not analyzer.openai_api_key and not args.allow_no_api:
        print("OPENAI_API_KEY is missing. Set it or use --allow-no-api.")
        return 1

    session = get_db_session()
    query = session.query(NewsArticle).order_by(NewsArticle.id.asc())
    if args.limit and args.limit > 0:
        query = query.limit(args.limit)

    articles = query.all()
    total = len(articles)
    updated = 0
    skipped = 0

    for article in articles:
        changed = False

        if args.include_title and article.title and analyzer._is_english_text(article.title):
            new_title = analyzer._translate_text(article.title, is_title=True)
            if new_title and new_title != article.title:
                article.title = new_title
                changed = True

        if args.include_content and article.content and analyzer._is_english_text(article.content):
            new_content = analyzer._translate_text(article.content, is_title=False)
            if new_content and new_content != article.content:
                article.content = new_content
                changed = True

                if args.update_summary:
                    article.summary = analyzer.summarize_article(new_content)

        if changed:
            updated += 1
            if args.dry_run:
                continue
            session.add(article)
        else:
            skipped += 1

    if args.dry_run:
        session.close()
        print(f"Dry run complete at {datetime.now().isoformat()}.")
        print(f"Total: {total}, Updated: {updated}, Skipped: {skipped}")
        return 0

    session.commit()
    session.close()

    print(f"Backfill complete at {datetime.now().isoformat()}.")
    print(f"Total: {total}, Updated: {updated}, Skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
