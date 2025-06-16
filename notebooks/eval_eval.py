import marimo

__generated_with = "0.13.15"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    from src.models.evaluation import ArticleEvaluation
    from src.models.post import BlueskyPost

    return ArticleEvaluation, BlueskyPost, mo


@app.cell
def _(BlueskyPost):
    posts = BlueskyPost.df_from_stage_dir("collect", days_back=30)
    posts
    return (posts,)


@app.cell
def _(mo, posts):
    tag_stats = (
        posts[["_file_name","tags"]]
        .explode("tags")
        .groupby("tags",as_index=False)
        .agg(num_rows=("_file_name","nunique"))
        .sort_values("num_rows", ascending=False)
                )
    mo.ui.table(tag_stats,page_size=30)
    return


@app.cell
def _(ArticleEvaluation):
    evals= ArticleEvaluation.df_from_stage_dir("evaluate", days_back=3)
    evals
    return (evals,)


@app.cell
def _():
    import pandas as pd
    parq = pd.read_parquet("parquet/collect/2025-06-16.parquet")
    return (parq,)


@app.cell
def _(parq):
    parq
    return


@app.cell
def _(evals, mo):
    kt = (
        evals.loc[lambda x: x["is_mcp_related"]]
        [["key_topics","_file_name"]]
        .explode("key_topics")
        .groupby("key_topics",as_index=False)
        .agg(num_rows = ("_file_name","nunique"))
        .sort_values("num_rows",ascending=False)
    )
    mo.ui.table(kt,page_size=30)
    return


if __name__ == "__main__":
    app.run()
