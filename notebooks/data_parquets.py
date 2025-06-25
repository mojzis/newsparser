import marimo

__generated_with = "0.13.15"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    return (pd,)


@app.cell
def _(pd):
    fetch = pd.read_parquet("parquet/fetch/by-run-date/2025-06-24_last_7_days.parquet")
    return (fetch,)


@app.cell
def _(pd):
    coll = pd.read_parquet("parquet/collect/by-run-date/2025-06-24_last_7_days.parquet")
    return (coll,)


@app.cell
def _(fetch):
    fetch
    return


@app.cell
def _(coll):
    coll
    return


@app.cell
def _(coll):
    coll.groupby("author").size().sort_values(ascending=False)
    return


if __name__ == "__main__":
    app.run()
