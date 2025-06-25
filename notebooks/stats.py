import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def __(mo):
    mo.md("# Bluesky MCP Monitor - Project Statistics")
    return


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    from pathlib import Path
    from datetime import datetime, date, timedelta
    import json
    from collections import defaultdict
    
    return Path, date, datetime, defaultdict, json, mo, pd, timedelta


@app.cell
def __(Path):
    # Define data directories
    stages_dir = Path("stages")
    output_dir = Path("output")
    parquet_dir = Path("parquet")
    
    return output_dir, parquet_dir, stages_dir


@app.cell
def __(mo, stages_dir):
    mo.md(f"""
    ## Data Collection Overview
    
    Analyzing data from the stage-based processing pipeline in `{stages_dir}`.
    """)
    return


@app.cell
def __(defaultdict, stages_dir):
    # Collect stage statistics
    stage_stats = defaultdict(lambda: defaultdict(int))
    
    if stages_dir.exists():
        for stage_name in ["collect", "fetch", "evaluate", "report"]:
            stage_path = stages_dir / stage_name
            if stage_path.exists():
                # Count files by date
                for date_dir in stage_path.iterdir():
                    if date_dir.is_dir() and date_dir.name.count("-") == 2:  # YYYY-MM-DD format
                        file_count = len(list(date_dir.glob("*.md"))) + len(list(date_dir.glob("*.html")))
                        stage_stats[stage_name][date_dir.name] = file_count
    
    return stage_stats,


@app.cell
def __(pd, stage_stats):
    # Create summary table data
    summary_data = []
    all_dates_summary = set()
    for summary_stage_name, summary_stage_dates in stage_stats.items():
        all_dates_summary.update(summary_stage_dates.keys())
    
    all_dates_summary = sorted(all_dates_summary, reverse=True)
    
    for date_str in all_dates_summary:
        row = {"Date": date_str}
        total = 0
        for summary_stage in ["collect", "fetch", "evaluate", "report"]:
            count = stage_stats[summary_stage].get(date_str, 0)
            row[summary_stage.title()] = count
            total += count
        row["Total"] = total
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    
    return all_dates_summary, summary_data, summary_df


@app.cell  
def __(stage_stats):
    # Calculate stage totals
    stage_totals = {}
    for totals_stage_name, totals_stage_dates in stage_stats.items():
        stage_totals[totals_stage_name] = sum(totals_stage_dates.values())
    
    return stage_totals,


@app.cell
def __(mo, summary_df):
    mo.md(f"""
    ### Daily Processing Summary
    
    {mo.as_html(summary_df.head(10))}
    
    **Total dates processed:** {len(summary_df)}
    """)
    return


@app.cell
def __(mo, stage_totals):
    mo.md(f"""
    ### Stage Totals
    
    - **Collect:** {stage_totals.get('collect', 0):,} posts
    - **Fetch:** {stage_totals.get('fetch', 0):,} URLs 
    - **Evaluate:** {stage_totals.get('evaluate', 0):,} evaluations
    - **Report:** {stage_totals.get('report', 0):,} reports
    """)
    return


@app.cell
def __(mo, output_dir):
    mo.md(f"""
    ## Generated Reports
    
    Reports generated in `{output_dir}/reports/`.
    """)
    return


@app.cell
def __(output_dir):
    # Count generated reports
    reports_dir = output_dir / "reports"
    report_dates = []
    
    if reports_dir.exists():
        for report_date_dir in reports_dir.iterdir():
            if report_date_dir.is_dir() and report_date_dir.name.count("-") == 2:
                report_file = report_date_dir / "report.html"
                if report_file.exists():
                    report_dates.append(report_date_dir.name)
    
    report_dates.sort(reverse=True)
    
    return report_dates, reports_dir


@app.cell
def __(report_dates):
    recent_reports = report_dates[:5] if report_dates else []
    return recent_reports,


@app.cell
def __(mo, report_dates, recent_reports):
    mo.md(f"""
    **Total reports generated:** {len(report_dates)}
    
    **Recent reports:**
    {chr(10).join(f"- {report_date}" for report_date in recent_reports) if recent_reports else "No reports found."}
    """)
    return


@app.cell
def __(mo, parquet_dir):
    mo.md(f"""
    ## Parquet Data Files
    
    Analytics data stored in `{parquet_dir}`.
    """)
    return


@app.cell
def __(parquet_dir):
    # Check parquet files
    parquet_stats = {}
    
    if parquet_dir.exists():
        for parquet_stage in ["collect", "fetch", "evaluate"]:
            stage_parquet_dir = parquet_dir / parquet_stage / "by-run-date"
            if stage_parquet_dir.exists():
                parquet_files = list(stage_parquet_dir.glob("*.parquet"))
                parquet_stats[parquet_stage] = {
                    "file_count": len(parquet_files),
                    "total_size_mb": sum(f.stat().st_size for f in parquet_files) / (1024 * 1024),
                    "latest_file": max(parquet_files, key=lambda x: x.stat().st_mtime).name if parquet_files else None
                }
    
    return parquet_stats,


@app.cell
def __(parquet_stats):
    parquet_info_list = []
    for parquet_stage_info, parquet_stats_info in parquet_stats.items():
        parquet_info_list.append(f"""
    **{parquet_stage_info.title()}:**
    - Files: {parquet_stats_info['file_count']}
    - Size: {parquet_stats_info['total_size_mb']:.1f} MB
    - Latest: {parquet_stats_info['latest_file'] or 'None'}
    """)
    
    return parquet_info_list,


@app.cell
def __(mo, parquet_info_list):
    mo.md("".join(parquet_info_list) if parquet_info_list else "No parquet files found.")
    return


@app.cell
def __(mo, output_dir):
    mo.md(f"""
    ## Additional Files
    
    Other generated files in `{output_dir}`.
    """)
    return


@app.cell
def __(datetime, output_dir):
    # Check for additional files
    additional_files = {}
    
    if output_dir.exists():
        # Check for main files
        main_files_to_check = ["index.html", "about.html", "rss.xml", "sitemap.xml"]
        
        for main_filename in main_files_to_check:
            filepath = output_dir / main_filename
            if filepath.exists():
                stat = filepath.stat()
                additional_files[main_filename] = {
                    "size_kb": stat.st_size / 1024,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                }
        
        # Check query directory
        query_dir = output_dir / "query"
        if query_dir.exists():
            query_html_files = list(query_dir.glob("*.html"))
            additional_files["query_files"] = len(query_html_files)
    
    return additional_files, main_files_to_check, query_dir, query_html_files


@app.cell
def __(additional_files):
    additional_file_info = []
    for additional_filename, additional_info in additional_files.items():
        if additional_filename == "query_files":
            additional_file_info.append(f"- **Query files:** {additional_info}")
        else:
            additional_file_info.append(f"- **{additional_filename}:** {additional_info['size_kb']:.1f} KB (modified: {additional_info['modified']})")
    
    return additional_file_info,


@app.cell
def __(additional_file_info, mo):
    mo.md("\n".join(additional_file_info) if additional_file_info else "No additional files found.")
    return


@app.cell
def __(datetime, mo):
    mo.md(f"""
    ## Summary
    
    **Statistics generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    This dashboard provides an overview of the Bluesky MCP Monitor project's data processing pipeline and output files.
    """)
    return


if __name__ == "__main__":
    app.run()