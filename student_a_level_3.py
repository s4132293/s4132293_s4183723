import pyhtml

def get_page_html(form_data=None):
    print("About to return Level 3A page...")
    db_path = "ps_milestone_immunization_data.db"

    antigen_rows = pyhtml.get_results_from_query(
        db_path,
        "SELECT AntigenID, name FROM Antigen ORDER BY name;"
    )

    yr_rows = pyhtml.get_results_from_query(
        db_path,
        "SELECT MIN(year), MAX(year) FROM Vaccination;"
    )
    if yr_rows and len(yr_rows[0]) == 2:
        min_year = int(yr_rows[0][0])
        max_year = int(yr_rows[0][1])
    else:
        min_year = 2000
        max_year = 2024

    default_antigen = antigen_rows[0][0] if antigen_rows else "DTPVCV1"
    default_start = min_year
    default_end = max_year
    default_top_n = 10

    if form_data is None:
        form_data = {}

    selected_antigen = form_data.get("antigen", [default_antigen])[0]
    selected_start = int(form_data.get("start_year", [str(default_start)])[0])
    selected_end = int(form_data.get("end_year", [str(default_end)])[0])
    selected_top_n = int(form_data.get("top_n", [str(default_top_n)])[0])

    if selected_start > selected_end:
        selected_start, selected_end = selected_end, selected_start

    improvement_query = f"""
        SELECT
            c.name AS country_name,
            v1.country AS country_code,
            '{selected_antigen}' AS antigen,
            {selected_start} AS start_year,
            {selected_end} AS end_year,
            ROUND(v1.coverage, 1) AS start_cov,
            ROUND(v2.coverage, 1) AS end_cov,
            ROUND(v2.coverage - v1.coverage, 1) AS improvement
        FROM Vaccination v1
        JOIN Vaccination v2
            ON v1.country = v2.country
           AND v1.antigen = v2.antigen
        JOIN Country c
            ON v1.country = c.CountryID
        WHERE v1.year = {selected_start}
          AND v2.year = {selected_end}
          AND v1.antigen = '{selected_antigen}'
        ORDER BY improvement DESC
        LIMIT {selected_top_n};
    """
    result_rows = pyhtml.get_results_from_query(db_path, improvement_query)

    antigen_options_html = ""
    for ag_id, ag_name in antigen_rows:
        antigen_options_html += f'<option value="{ag_id}"'
        if ag_id == selected_antigen:
            antigen_options_html += ' selected'
        antigen_options_html += f'>{ag_name}</option>'

    year_options_start_html = ""
    year_options_end_html = ""
    for y in range(max_year, min_year - 1, -1):
        start_sel = " selected" if y == selected_start else ""
        end_sel = " selected" if y == selected_end else ""
        year_options_start_html += f'<option value="{y}"{start_sel}>{y}</option>'
        year_options_end_html += f'<option value="{y}"{end_sel}>{y}</option>'

    top_n_options_html = ""
    for n in [5, 10, 15, 20, 30]:
        sel = " selected" if n == selected_top_n else ""
        top_n_options_html += f'<option value="{n}"{sel}>{n}</option>'

    selected_antigen_name = next(
        (ag_name for ag_id, ag_name in antigen_rows if ag_id == selected_antigen),
        selected_antigen
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Vaccination Data Dashboard - Level 3A</title>
    <link rel="stylesheet" href="style.css">
    <style>
        body {{
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background-color: #f4f4f4;
        }}
        .topnav {{
            overflow: hidden;
            background-color: #333;
        }}
        .topnav a {{
            float: left;
            display: block;
            color: #f2f2f2;
            text-align: center;
            padding: 10px 16px;
            text-decoration: none;
            font-size: 14px;
        }}
        .topnav a:hover {{
            background-color: #ddd;
            color: black;
        }}
        .header-image {{
            width: 100%;
            height: 120px;
            background-image: url('header.jpg');
            background-size: cover;
            background-position: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding-left: 15px;
            color: #fff;
        }}
        .header-title {{
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 6px;
        }}
        .header-subtitle {{
            font-size: 12px;
        }}
        .page-container {{
            padding: 15px;
        }}
        h2 {{
            font-size: 18px;
        }}
        .filter-row {{
            margin-bottom: 10px;
            font-size: 14px;
        }}
        select {{
            padding: 3px 5px;
            font-size: 13px;
        }}
        .btn-small {{
            padding: 4px 10px;
            font-size: 13px;
            cursor: pointer;
        }}
        .tables-wrapper {{
            display: flex;
            gap: 20px;
            align-items: flex-start;
        }}
        .main-table {{
            background: #fff;
            border: 1px solid #d0d0d0;
            flex: 1 1 65%;
        }}
        .side-table {{
            background: #fff;
            border: 1px solid #d0d0d0;
            width: 30%;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #d0d0d0;
            padding: 5px 7px;
        }}
        th {{
            background-color: #003b63;
            color: #fff;
            font-weight: normal;
            text-align: left;
        }}
        .footer {{
            background-color: #003b63;
            color: #fff;
            text-align: center;
            padding: 10px;
            margin-top: 15px;
        }}
        .howto-box {{
            background-color: #dfe9f2;
            border: 1px solid #acc5d9;
            border-radius: 6px;
            margin-top: 16px;
            padding: 15px;
        }}
        .howto-title {{
            text-align: center;
            font-size: 14px;
            margin-bottom: 10px;
            color: #003b63;
        }}
        .howto-steps {{
            display: flex;
            justify-content: space-around;
            text-align: center;
        }}
        .howto-step-number {{
            width: 22px;
            height: 22px;
            border-radius: 50%;
            border: 2px solid #003b63;
            color: #003b63;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            margin-bottom: 5px;
        }}
        .howto-step-text {{
            font-size: 12px;
            max-width: 280px;
        }}
    </style>
</head>
<body>

    <div class="topnav">
        <a href="/">Home</a>
        <a href="/level2a">Explore</a>
        <a class="/active" href="/level3a">Deep Dive</a>
        <a href="/level1b">Summary</a>
        <a href="/level2b">Compare</a>
        <a href="/level3b">Insights</a>
    </div>

    <div class="header-image">
        <div class="header-title">Vaccination Data Dashboard</div>
        <div class="header-subtitle">Deep dive: biggest improvements in vaccination coverage.</div>
    </div>

    <div class="page-container">
        <h2>Countries with biggest improvement in vaccination coverage</h2>

        <form action="/level3a" method="GET">
            <div class="filter-row">
                Antigen:
                <select name="antigen">{antigen_options_html}</select>
                Start year:
                <select name="start_year">{year_options_start_html}</select>
                End year:
                <select name="end_year">{year_options_end_html}</select>
                Show top:
                <select name="top_n">{top_n_options_html}</select>
                <input type="submit" value="Update" class="btn-small">
            </div>
        </form>

        <div class="tables-wrapper">
            <div class="main-table">
                <table>
                    <tr>
                        <th>Country</th>
                        <th>Start cov ({selected_start})</th>
                        <th>End cov ({selected_end})</th>
                        <th>Improvement</th>
                        <th>Antigen</th>
                    </tr>
    """

    if result_rows:
        for row in result_rows:
            country_name, _, _, _, _, start_cov, end_cov, improvement = row
            html += f"""
                    <tr>
                        <td>{country_name}</td>
                        <td>{start_cov}</td>
                        <td>{end_cov}</td>
                        <td>{improvement}</td>
                        <td>{selected_antigen_name}</td>
                    </tr>
            """
    else:
        html += """<tr><td colspan="5">No data found for this selection.</td></tr>"""

    html += f"""
                </table>
            </div>

            <div class="side-table">
                <table>
                    <tr><th colspan="2">Selection summary</th></tr>
                    <tr><td>Antigen</td><td>{selected_antigen_name}</td></tr>
                    <tr><td>Start year</td><td>{selected_start}</td></tr>
                    <tr><td>End year</td><td>{selected_end}</td></tr>
                    <tr><td>Top N</td><td>{selected_top_n}</td></tr>
                    <tr><td>Rows returned</td><td>{len(result_rows)}</td></tr>
                </table>
            </div>
        </div>

        <div class="howto-box">
            <div class="howto-title">How to use this page</div>
            <div class="howto-steps">
                <div>
                    <div class="howto-step-number">1</div>
                    <div class="howto-step-text">
                        Pick the antigen and the time window (start and end year) you want to compare.
                    </div>
                </div>
                <div>
                    <div class="howto-step-number">2</div>
                    <div class="howto-step-text">
                        Choose how many countries to list and click Update to run the deep-dive query.
                    </div>
                </div>
                <div>
                    <div class="howto-step-number">3</div>
                    <div class="howto-step-text">
                        Read the main table to see who improved the most. The bigger the improvement, the higher the row.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        Data source: WHO Immunisation Database
    </div>

</body>
</html>
"""
    return html
