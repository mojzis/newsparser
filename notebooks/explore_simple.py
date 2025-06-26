import marimo

__generated_with = "0.13.15"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent / "src"))

    from config.settings import Settings
    from storage.r2_client import R2Client

    return R2Client, Settings, mo, pd


@app.cell
def _(mo):
    mo.md("""# Simple Data Explorer""")
    return


@app.cell
def _(R2Client, Settings, mo):
    settings = Settings()
    r2_client = R2Client(settings)
    mo.md("R2 client initialized")
    return r2_client, settings


@app.cell
def _(settings):
    settings
    return


@app.cell
def _(mo, r2_client):
    from datetime import date, timedelta

    # Try today's date first, then yesterday
    today = date.today()
    yesterday = today - timedelta(days=1)

    dates_to_try = [today, yesterday]
    available_files = {}

    for date_to_check in dates_to_try:
        date_str = date_to_check.strftime("%Y-%m-%d")

        # Check each file type
        file_patterns = {
            "posts": f"parquet/collect/by-run-date/{date_str}_last_7_days.parquet",
            "fetched": f"parquet/fetch/by-run-date/{date_str}_last_7_days.parquet", 
            "evaluated": f"parquet/evaluate/by-run-date/{date_str}_last_7_days.parquet"
        }

        for file_type, file_path in file_patterns.items():
            if file_type not in available_files and r2_client.file_exists(file_path):
                available_files[file_type] = file_path

        # If we found all types, no need to check yesterday
        if len(available_files) == 3:
            break

    files_status = f"""
    **Available Files for {today.strftime("%Y-%m-%d")} / {yesterday.strftime("%Y-%m-%d")}:**
    - Posts: {'✅' if 'posts' in available_files else '❌'}
    - Fetched: {'✅' if 'fetched' in available_files else '❌'}
    - Evaluated: {'✅' if 'evaluated' in available_files else '❌'}
    """

    mo.md(files_status)
    return available_files, file_patterns


@app.cell
def _(file_patterns):
    file_patterns

    return


@app.cell
def _(r2_client):
    r2_client.file_exists("parquet/collect/by-run-date/2025-06-26_last_7_days.parquet")
    return


@app.cell
def _(available_files, mo, pd, r2_client):
    import io

    if "evaluated" in available_files:
        # Download evaluated file directly to memory
        key = available_files["evaluated"]
        data_bytes = r2_client.download_bytes(key)
        df = pd.read_parquet(io.BytesIO(data_bytes))

        load_status = f"Loaded {df.shape[0]} rows from {key}"
    else:
        df = pd.DataFrame()
        load_status = "No evaluated data files available for today or yesterday"

    # Display OUTSIDE control blocks
    mo.md(load_status)
    return (df,)


@app.cell
def _(df, mo):
    if not df.empty:
        display_element = mo.ui.table(df.head(10), label="Data Sample")
    else:
        display_element = mo.md("No data to display")

    # Display OUTSIDE control blocks
    display_element
    return


if __name__ == "__main__":
    app.run()
