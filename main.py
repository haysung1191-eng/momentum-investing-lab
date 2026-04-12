import os
from datetime import datetime

from screener import MomentumScreener


def main():
    mode = os.environ.get("SCREENER_MODE", "STOCK").upper()
    etf_mode = mode == "ETF"

    print("====================================")
    print("KIS API ETF 모멘텀 스크리너 시작" if etf_mode else "KIS API 모멘텀 스크리너 시작")

    try:
        screener = MomentumScreener()
    except Exception as e:
        print(f"API 초기화 실패: {e}")
        print(".env 파일의 APP_KEY, APP_SECRET을 확인해 주세요.")
        return

    df = screener.run(etf_mode=etf_mode)

    if df is None or df.empty:
        print("스크리닝 결과가 없습니다.")
        return

    import config

    prefix = "etf_results" if etf_mode else "momentum_results"
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    use_gcs = bool(getattr(config, "GCS_BUCKET_NAME", None))

    if use_gcs:
        filepath = f"gs://{config.GCS_BUCKET_NAME}/{filename}"
        try:
            df.to_excel(filepath, index=False)
            print(f"\n결과가 GCS에 저장되었습니다: {filepath}")
            return
        except Exception as e:
            print(f"\nGCS 저장 실패, 로컬 저장으로 전환합니다: {e}")

    desktop = os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")
    filepath = os.path.join(desktop, filename)
    df.to_excel(filepath, index=False)
    print(f"\n결과가 저장되었습니다: {filepath}")


if __name__ == "__main__":
    main()
