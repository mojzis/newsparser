import marimo

__generated_with = "0.13.15"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    from src.stages.report import ReportStage
    from datetime import date
    import pandas as pd
    return ReportStage, date, pd


@app.cell
def _(ReportStage, date):
    data = ReportStage().collect_mcp_articles_multi_day(days_back=7,reference_date =date(2025,6,16) )
    return (data,)


@app.cell
def _(data):
    data[0].model_dump_json()
    return


@app.cell
def _(data, pd):
    df = pd.DataFrame([d.model_dump() for d in data])
    df
    return


if __name__ == "__main__":
    app.run()
