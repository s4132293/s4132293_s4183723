import sqlite3

DB_PATH = "ps_milestone_immunization_data.db"


def get_page_html(form_data=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT AntigenID, name FROM Antigen ORDER BY name;")
    antigen_rows = cur.fetchall()

    cur.execute("SELECT DISTINCT year FROM InfectionData ORDER BY year DESC;")
    year_rows = cur.fetchall()

    default_antigen = antigen_rows[0][0] if antigen_rows else ""
    default_year = year_rows[0][0] if year_rows else 2024

    selected_antigen = default_antigen
    selected_year = default_year

    if form_data:
        ag_val = form_data.get("antigen", [default_antigen])
        if isinstance(ag_val, list):
            ag_val = ag_val[0]
        selected_antigen = ag_val or default_antigen

        yr_val = form_data.get("year", [default_year])
        if isinstance(yr_val, list):
            yr_val = yr_val[0]
        try:
            selected_year = int(yr_val)
        except Exception:
            selected_year = default_year

    antigen_name_lookup = {row[0]: row[1] for row in antigen_rows}
    selected_antigen_name = antigen_name_lookup.get(selected_antigen, selected_antigen)

    cur.execute(
        """
        SELECT v.antigen,
               v.year,
               c.name AS country_name,
               v.coverage
        FROM Vaccination v
        JOIN Country c ON v.country = c.CountryID
        WHERE v.antigen = ?
          AND v.year = ?
          AND v.coverage >= 90
        ORDER BY c.name
        """,
        (selected_antigen, selected_year),
    )
    table1_rows = cur.fetchall()

    cur.execute(
        """
        SELECT c.region AS region_code,
               COUNT(*) AS countries_ge90
        FROM Vaccination v
        JOIN Country c ON v.country = c.CountryID
        WHERE v.antigen = ?
          AND v.year = ?
          AND v.coverage >= 90
        GROUP BY c.region
        ORDER BY c.region
        """,
        (selected_antigen, selected_year),
    )
    table2_rows = cur.fetchall()

    conn.close()

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Vaccination Data Dashboard</title>
    <link rel="stylesheet" href="style.css">
    <style>
        body {{ margin:0; font-family: Arial, Helvetica, sans-serif; background:#f2f2f2; }}
        .topnav {{
            overflow: hidden;
            background-color: #333;
            height: 30px;
        }}
        .topnav a {{
            float: left;
            display: block;
            color: #f2f2f2;
            text-align: center;
            padding: 6px 14px;
            text-decoration: none;
            font-size: 14px;
        }}
        .topnav a.active {{ background-color: #111; }}
        .header-image {{
            width: 100%;
            height: 120px;
            background-image: url('header.jpg');
            background-size: cover;
            background-position: center;
            position: relative;
        }}
        .header-overlay {{
            position: absolute;
            inset: 0;
            background: rgba(2, 36, 73, 0.45);
            color: #fff;
            padding: 24px 14px;
        }}
        .header-overlay h1 {{ margin:0; font-size: 20px; }}
        .header-overlay p {{ margin:4px 0 0 0; font-size: 12px; }}
        .page-body {{ padding: 12px 14px 50px 14px; }}
        .filters label {{ margin-right:6px; }}
        .filters select {{ margin-right:6px; }}
        .tables-row {{
            display: flex;
            gap: 28px;
            margin-top: 18px;
            align-items: flex-start;
        }}
        table.data-table {{
            border-collapse: collapse;
            background: #fff;
            font-size: 13px;
        }}
        table.data-table th,
        table.data-table td {{
            border: 1px solid #ccc;
            padding: 4px 7px;
        }}
        table.data-table th {{
            background: #0d3b66;
            color: #fff;
        }}
        .table1-wrapper {{
            flex: 0 0 70%;
            min-width: 600px;
        }}
        .table2-wrapper {{
            flex: 0 0 26%;
            min-width: 240px;
        }}

        /* how-to panel (same vibe as home) */
        .howto-box {{
            background: #e9f0f5;
            border: 1px solid #c9d8e4;
            border-radius: 8px;
            margin-top: 26px;
            padding: 18px 14px 14px 14px;
        }}
        .howto-title {{
            text-align: center;
            color: #0d3b66;
            font-weight: bold;
            margin-bottom: 12px;
        }}
        .howto-steps {{
            display: flex;
            justify-content: space-around;
            gap: 16px;
        }}
        .howto-step {{
            text-align: center;
            flex: 1 1 0;
            font-size: 12px;
        }}
        .howto-number {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            border: 2px solid #0d73c6;
            color: #0d73c6;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 6px;
        }}

        .footer {{
            background: #003866;
            color: #fff;
            text-align: center;
            padding: 10px 5px;
            font-size: 12px;
            margin-top: 35px;
        }}
        @media (max-width: 1100px) {{
            .tables-row {{
                flex-direction: column;
            }}
            .table1-wrapper, .table2-wrapper {{
                flex: 1 1 100%;
                min-width: auto;
            }}
            .howto-steps {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="topnav">
        <a href="/">Home</a>
        <a class="active" href="/level2a">Explore</a>
        <a href="/level3a">Deep Dive</a>
        <a href="/level1b">Summary</a>
        <a href="/level2b">Compare</a>
        <a href="/level3b">Insights</a>
    </div>

    <div class="header-image">
        <div class="header-overlay">
            <h1>Vaccination Data Dashboard</h1>
            <p>Explore country-level coverage by antigen and year.</p>
        </div>
    </div>

    <div class="page-body">
        <h2>Countries meeting ≥ 90% coverage</h2>

        <form method="get" class="filters">
            <label for="antigen">Antigen:</label>
            <select id="antigen" name="antigen">
"""
    for ag_id, ag_name in antigen_rows:
        selected_attr = " selected" if ag_id == selected_antigen else ""
        html += f'<option value="{ag_id}"{selected_attr}>{ag_name}</option>'

    html += """
            </select>

            <label for="year">Year:</label>
            <select id="year" name="year">
"""
    for (yr,) in year_rows:
        selected_attr = " selected" if yr == selected_year else ""
        html += f'<option value="{yr}"{selected_attr}>{yr}</option>'

    html += """
            </select>

            <button type="submit">Update</button>
        </form>

        <div class="tables-row">
            <!-- TABLE 1 -->
            <div class="table1-wrapper">
                <h3>Table 1: Countries ≥ 90% (""" + f"{selected_antigen_name}, {selected_year}" + """)</h3>
                <table class="data-table" style="width:100%;">
                    <tr>
                        <th>Antigen</th>
                        <th>Year</th>
                        <th>Country</th>
                        <th>Coverage (%)</th>
                    </tr>
"""
    if table1_rows:
        for row in table1_rows[:20]:
            ag, yr, country_name, coverage = row
            try:
                coverage_str = f"{float(coverage):.1f}"
            except Exception:
                coverage_str = str(coverage)
            html += f"""
                    <tr>
                        <td>{ag}</td>
                        <td>{yr}</td>
                        <td>{country_name}</td>
                        <td style="text-align:right;">{coverage_str}</td>
                    </tr>
            """
        if len(table1_rows) > 20:
            html += f"""
                    <tr>
                        <td colspan="4" style="font-size:11px;">
                            Showing first 20 of {len(table1_rows)} countries for this selection.
                        </td>
                    </tr>
            """
    else:
        html += """
                    <tr>
                        <td colspan="4">No countries reached 90% for this selection.</td>
                    </tr>
        """

    html += """
                </table>
            </div>

            <!-- TABLE 2 -->
            <div class="table2-wrapper">
                <h3>Table 2: Count by Region (""" + f"{selected_antigen_name}, {selected_year}" + """)</h3>
                <table class="data-table" style="width:100%;">
                    <tr>
                        <th>Region / code</th>
                        <th>Countries ≥ 90%</th>
                    </tr>
"""
    if table2_rows:
        for region_code, cnt in table2_rows:
            display_region = region_code if region_code else "Unknown"
            html += f"""
                    <tr>
                        <td>{display_region}</td>
                        <td style="text-align:right;">{cnt}</td>
                    </tr>
            """
    else:
        html += """
                    <tr>
                        <td colspan="2">No regions have countries at ≥ 90% for this selection.</td>
                    </tr>
        """
    html += """
                </table>
            </div>
        </div>

        <!-- how to use -->
        <div class="howto-box">
            <div class="howto-title">How to use this page</div>
            <div class="howto-steps">
                <div class="howto-step">
                    <div class="howto-number">1</div>
                    Choose an antigen and year from the dropdowns above.
                </div>
                <div class="howto-step">
                    <div class="howto-number">2</div>
                    Click <strong>Update</strong> to refresh Table 1 with the countries that reached ≥ 90% coverage.
                </div>
                <div class="howto-step">
                    <div class="howto-number">3</div>
                    Read Table 2 to see how many countries in each region hit the same target.
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
