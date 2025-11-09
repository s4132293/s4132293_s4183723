import sqlite3

DB_PATH = "ps_milestone_immunization_data.db"


def get_page_html(form_data=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, description FROM Infection_Type ORDER BY description;")
    inf_rows = cur.fetchall()

    cur.execute("SELECT DISTINCT year FROM InfectionData ORDER BY year DESC;")
    year_rows = cur.fetchall()

    sel_inf = inf_rows[0][0] if inf_rows else ""
    sel_year = year_rows[0][0] if year_rows else 2024

    if form_data:
        inf_val = form_data.get("infection", [sel_inf])
        if isinstance(inf_val, list):
            inf_val = inf_val[0]
        if inf_val:
            sel_inf = inf_val

        year_val = form_data.get("year", [sel_year])
        if isinstance(year_val, list):
            year_val = year_val[0]
        try:
            sel_year = int(year_val)
        except Exception:
            sel_year = year_rows[0][0] if year_rows else 2024

    cur.execute(
        """
        SELECT
            SUM(idt.cases) AS total_cases,
            SUM(CASE
                    WHEN cp.population IS NOT NULL AND cp.population > 0
                    THEN cp.population
                    ELSE 0
                END) AS total_pop
        FROM InfectionData idt
        LEFT JOIN CountryPopulation cp
               ON cp.country = idt.country AND cp.year = idt.year
        WHERE idt.inf_type = ?
          AND idt.year = ?;
        """,
        (sel_inf, sel_year),
    )
    total_cases, total_pop = cur.fetchone()
    if not total_cases:
        total_cases = 0
    if not total_pop or total_pop == 0:
        global_rate = None
    else:
        global_rate = (total_cases / total_pop) * 100000

    cur.execute(
        """
        SELECT
            c.name AS country_name,
            idt.cases,
            cp.population
        FROM InfectionData idt
        JOIN Country c ON idt.country = c.CountryID
        LEFT JOIN CountryPopulation cp
               ON cp.country = idt.country AND cp.year = idt.year
        WHERE idt.inf_type = ?
          AND idt.year = ?
        ORDER BY c.name;
        """,
        (sel_inf, sel_year),
    )
    rows = cur.fetchall()
    conn.close()

    exceeding_rows = []
    if global_rate is not None and rows:
        for country_name, cases, pop in rows:
            if pop and pop > 0:
                rate_100k = (cases / pop) * 100000
                if rate_100k > global_rate:
                    exceeding_rows.append(
                        (country_name, cases, pop, rate_100k)
                    )

    inf_lookup = {str(i): d for i, d in inf_rows}
    sel_inf_name = inf_lookup.get(str(sel_inf), str(sel_inf))

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Vaccination Data Dashboard - Insights</title>
    <link rel="stylesheet" href="style.css">
    <style>
        body {{
            margin:0;
            font-family: Arial, Helvetica, sans-serif;
            background:#f2f2f2;
        }}
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
        .page-body {{ padding: 14px 14px 40px 14px; }}

        .panel {{
            background:#fff;
            border:1px solid #dcdcdc;
            border-radius:4px;
            padding:10px;
            margin-bottom:16px;
        }}
        .filters {{
            display:flex;
            gap:12px;
            flex-wrap:wrap;
            align-items:center;
        }}
        .filters label {{
            font-size:13px;
        }}
        .filters select {{
            margin-left:4px;
        }}
        table.data-table {{
            border-collapse: collapse;
            width: 100%;
            background:#fff;
            font-size: 13px;
        }}
        table.data-table th,
        table.data-table td {{
            border: 1px solid #ccc;
            padding: 4px 6px;
        }}
        table.data-table th {{
            background: #0d3b66;
            color: #fff;
            text-align:left;
        }}
        .footer {{
            background: #003866;
            color: #fff;
            text-align: center;
            padding: 10px 5px;
            font-size: 12px;
            margin-top: 28px;
        }}
        .howto-box {{
            background: #e9f0f5;
            border: 1px solid #c9d8e4;
            border-radius: 8px;
            margin-top: 14px;
            padding: 10px 14px;
        }}
        .howto-steps {{
            display:flex;
            gap:12px;
            justify-content:space-around;
        }}
        .howto-step {{
            font-size:12px;
            text-align:center;
            flex:1 1 0;
        }}
        .howto-number {{
            width:26px;
            height:26px;
            border-radius:50%;
            border:2px solid #0d73c6;
            color:#0d73c6;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            margin-bottom:4px;
            font-weight:bold;
        }}
        @media (max-width: 900px) {{
            .filters {{ flex-direction:column; align-items:flex-start; }}
            .howto-steps {{ flex-direction:column; }}
        }}
    </style>
</head>
<body>
    <div class="topnav">
        <a href="/">Home</a>
        <a href="/level2a">Explore</a>
        <a href="/level3a">Deep Dive</a>
        <a href="/level1b">Summary</a>
        <a href="/level2b">Compare</a>
        <a class="active" href="/level3b">Insights</a>
    </div>

    <div class="header-image">
        <div class="header-overlay">
            <h1>Vaccination Data Dashboard</h1>
            <p>Insights: countries above the global infection rate.</p>
        </div>
    </div>

    <div class="page-body">
        <h2 style="margin:0 0 10px 0;">Countries exceeding global infection rate</h2>

        <div class="panel">
            <form method="get" class="filters">
                <label>Infection:
                    <select name="infection">
"""
    for inf_id, desc in inf_rows:
        selected = " selected" if str(inf_id) == str(sel_inf) else ""
        html += f'<option value="{inf_id}"{selected}>{desc}</option>'
    html += """
                    </select>
                </label>
                <label>Year:
                    <select name="year">
"""
    for (yr,) in year_rows:
        selected = " selected" if yr == sel_year else ""
        html += f'<option value="{yr}"{selected}>{yr}</option>'
    html += """
                    </select>
                </label>
                <button type="submit">Update</button>
            </form>
        </div>

        <div class="panel">
            <h3>Global infection rate</h3>
            <table class="data-table">
                <tr>
                    <th>Infection</th>
                    <th>Year</th>
                    <th>Global rate / 100k</th>
                </tr>
                <tr>
                    <td>""" + sel_inf_name + """</td>
                    <td>""" + str(sel_year) + """</td>
                    <td>""" + (f"{global_rate:.2f}" if global_rate is not None else "-") + """</td>
                </tr>
            </table>
            <p style="font-size:11px; margin-top:6px;">
                Note: global rate is based only on rows that have population for this infection and year.
            </p>
        </div>

        <div class="panel">
            <h3>Countries exceeding global rate</h3>
            <table class="data-table">
                <tr>
                    <th>Country</th>
                    <th>Cases</th>
                    <th>Population</th>
                    <th>Rate / 100k</th>
                </tr>
"""
    if global_rate is None:
        html += """
                <tr><td colspan="4">Not enough population data to compute a global rate for this selection.</td></tr>
"""
    else:
        if exceeding_rows:
            for country_name, cases, pop, rate_100k in exceeding_rows:
                pop_str = f"{int(pop):,}" if pop else "-"
                html += f"""
                <tr>
                    <td>{country_name}</td>
                    <td>{cases}</td>
                    <td>{pop_str}</td>
                    <td>{rate_100k:.2f}</td>
                </tr>
"""
        else:
            html += """
                <tr><td colspan="4">No countries above global rate.</td></tr>
"""
    html += """
            </table>
        </div>

        <div class="howto-box">
            <div class="howto-steps">
                <div class="howto-step">
                    <div class="howto-number">1</div>
                    Pick an infection and year to analyse.
                </div>
                <div class="howto-step">
                    <div class="howto-number">2</div>
                    We calculate the global rate from all countries that have population.
                </div>
                <div class="howto-step">
                    <div class="howto-number">3</div>
                    Countries listed above are the ones doing worse than that rate.
                </div>
            </div>
        </div>
    </div>

    <div class="footer">Data source: WHO Immunisation Database</div>
</body>
</html>
"""
    return html
