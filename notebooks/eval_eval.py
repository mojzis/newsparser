import marimo

__generated_with = "0.13.15"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    from src.models.evaluation import ArticleEvaluation
    from src.models.post import BlueskyPost

    return ArticleEvaluation, BlueskyPost


@app.cell
def _(BlueskyPost):
    posts = BlueskyPost.df_from_stage_dir("collect", days_back=3)
    return


@app.cell
def _(ArticleEvaluation):
    evals= ArticleEvaluation.df_from_stage_dir("evaluate", days_back=3)
    evals
    return


if __name__ == "__main__":
    app.run()
