import argparse

import config
from kis_backtest_from_prices import write_csv_any
from kis_shadow_common import compute_target_portfolio, default_backtests_base, read_json_any, resolve_strategy_name


def main() -> None:
    default_base = default_backtests_base()
    p = argparse.ArgumentParser(description="Generate the current target shadow portfolio for one selected strategy.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--live-readiness-path", type=str, default=f"{default_base}/kis_live_readiness.csv")
    p.add_argument("--manifest-path", type=str, default=f"{default_base}/kis_pipeline_run_manifest.json")
    p.add_argument("--strategy-name", type=str, default="")
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_shadow_portfolio.csv")
    p.add_argument("--as-of-date", type=str, default="")
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--max-files", type=int, default=0)
    args = p.parse_args()

    manifest = read_json_any(args.manifest_path)
    strategy_name = resolve_strategy_name(args.live_readiness_path, args.strategy_name or None)
    portfolio, meta = compute_target_portfolio(
        base=args.base,
        strategy_name=strategy_name,
        min_common_dates=args.min_common_dates,
        as_of_date=args.as_of_date or None,
        manifest_path=args.manifest_path,
        max_files=args.max_files,
    )
    portfolio.insert(0, "Strategy", strategy_name)
    portfolio.insert(0, "RunStartedAt", manifest.get("started_at"))
    portfolio.insert(0, "RunId", manifest.get("run_id"))
    write_csv_any(portfolio, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(f"strategy={strategy_name} as_of={meta['AsOfDate']} holdings={meta['HoldingsCount']} weight_sum={meta['WeightSum']:.6f}")
    print("\n=== Shadow Portfolio ===")
    print(portfolio.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
