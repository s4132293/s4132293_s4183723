import sqlite3

DB_PATH = "ps_milestone_immunization_data.db"


def get_page_html(form_data=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, description FROM Infection_Type ORDER BY description;")
    inf_rows = cur.fetchall()

    cur.execute("SELECT DISTINCT year FROM InfectionData ORDER BY year DESC;")
    year_rows = cur.fetchall()

    cur.execute("SELECT economyID, phase FROM Economy ORDER BY economyID;")
    econ_rows = cur.fetchall()

    sel_inf = inf_rows[0][0] if inf_rows else ""
    sel_year = year_rows[0][0] if year_rows else 2024
    sel_econ = "all"

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

        econ_val = form_data.get("economy", [sel_econ])
        if isinstance(econ_val, list):
            econ_val = econ_val[0]
        if econ_val:
            sel_econ = econ_val

    params = [sel_inf, sel_year]
    econ_filter_sql = ""
    if sel_econ != "all":
        econ_filter_sql = "AND c.economy = ?"
        params.append(sel_econ)

    cur.execute(
        f"""
        SELECT
            c.name AS country_name,
            e.phase AS econ_phase,
            it.description AS infection_name,
            idt.year,
            idt.cases,
            cp.population
        FROM InfectionData idt
        JOIN Infection_Type it ON idt.inf_type = it.id
        JOIN Country c ON idt.country = c.CountryID
        LEFT JOIN CountryPopulation cp
               ON cp.country = idt.country AND cp.year = idt.year
        LEFT JOIN Economy e ON c.economy = e.economyID
        WHERE idt.inf_type = ?
          AND idt.year = ?
          {econ_filter_sql}
        ORDER BY c.name;
        """,
        params,
    )
    country_rows = cur.fetchall()

    rows_countries = []
    for country_name, econ_phase, infection_name, year, cases, pop in country_rows:
        if pop and pop > 0:
            rate_100k = (cases / pop) * 100000
        else:
            rate_100k = None
        rows_countries.append(
            (country_name, econ_phase, infection_name, year, cases, pop, rate_100k)
        )

    params_sum = [sel_inf, sel_year]
    econ_filter_sql_sum = ""
    if sel_econ != "all":
        econ_filter_sql_sum = "AND c.economy = ?"
        params_sum.append(sel_econ)

    cur.execute(
        f"""
        SELECT
            e.phase AS econ_phase,
            idt.year,
            SUM(idt.cases) AS total_cases
        FROM InfectionData idt
        JOIN Country c ON idt.country = c.CountryID
        LEFT JOIN Economy e ON c.economy = e.economyID
        WHERE idt.inf_type = ?
          AND idt.year = ?
          {econ_filter_sql_sum}
        GROUP BY e.phase, idt.year
        ORDER BY e.phase;
        """,
        params_sum,
    )
    rows_summary = cur.fetchall()

    conn.close()

    inf_name_lookup = {str(i): d for i, d in inf_rows}
    sel_inf_name = inf_name_lookup.get(str(sel_inf), str(sel_inf))

    econ_name_lookup = {str(eid): ph for eid, ph in econ_rows}
    sel_econ_label = "All economies" if sel_econ == "all" else econ_name_lookup.get(str(sel_econ), str(sel_econ))

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Vaccination Data Dashboard - Compare</title>
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
            padding:10px 10px 6px 10px;
            margin-bottom:18px;
        }}
        .filters {{
            display:flex;
            gap:12px;
            flex-wrap:wrap;
            align-items:center;
            margin-bottom:8px;
        }}
        .filters label {{
            font-size:13px;
        }}
        .filters select {{
            margin-left:4px;
        }}
        h2.title-bar {{
            margin:0 0 10px 0;
            font-size:16px;
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
        <a class="active" href="/level2b">Compare</a>
        <a href="/level3b">Insights</a>
    </div>

    <div class="header-image">
        <div class="header-overlay">
            <h1>Vaccination Data Dashboard</h1>
            <p>Compare infection totals by economy, infection type, and year.</p>
        </div>
    </div>

    <div class="page-body">
        <h2 class="title-bar">Compare infection data</h2>

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
                <label>Economy:
                    <select name="economy">
                        <option value="all" """ + ("selected" if sel_econ == "all" else "") + """>All</option>
"""
    for econ_id, phase in econ_rows:
        selected = " selected" if str(econ_id) == str(sel_econ) else ""
        html += f'<option value="{econ_id}"{selected}>{phase}</option>'
    html += """
                    </select>
                </label>
                <button type="submit">Update</button>
            </form>
        </div>

        <div class="panel">
            <h3>Countries (""" + f"{sel_inf_name}, {sel_year}, {sel_econ_label}" + """)</h3>
            <table class="data-table">
                <tr>
                    <th>Country</th>
                    <th>Economic phase</th>
                    <th>Infection</th>
                    <th>Year</th>
                    <th>Cases</th>
                    <th>Population</th>
                    <th>Cases / 100k</th>
                </tr>
"""
    if rows_countries:
        for country_name, econ_phase, infection_name, year, cases, pop, rate_100k in rows_countries:
            rate_str = f"{rate_100k:.1f}" if rate_100k is not None else "-"
            pop_str = f"{int(pop):,}" if pop else "-"
            html += f"""
                <tr>
                    <td>{country_name}</td>
                    <td>{econ_phase or '-'}</td>
                    <td>{infection_name}</td>
                    <td>{year}</td>
                    <td>{cases}</td>
                    <td>{pop_str}</td>
                    <td>{rate_str}</td>
                </tr>
"""
    else:
        html += """
                <tr><td colspan="7">No records found for this selection.</td></tr>
"""
    html += """
            </table>
        </div>

        <div class="panel">
            <h3>Summary by economic phase</h3>
            <table class="data-table">
                <tr>
                    <th>Economic phase</th>
                    <th>Year</th>
                    <th>Total cases</th>
                </tr>
"""
    if rows_summary:
        for phase, yr, total in rows_summary:
            html += f"""
                <tr>
                    <td>{phase or '-'}</td>
                    <td>{yr}</td>
                    <td>{total}</td>
                </tr>
"""
    else:
        html += """
                <tr><td colspan="3">No summary data available.</td></tr>
"""
    html += """
            </table>
        </div>

        <div class="howto-box">
            <div class="howto-steps">
                <div class="howto-step">
                    <div class="howto-number">1</div>
                    Pick an infection, year, and (optionally) an economy group.
                </div>
                <div class="howto-step">
                    <div class="howto-number">2</div>
                    Click Update to refresh the country list and summary.
                </div>
                <div class="howto-step">
                    <div class="howto-number">3</div>
                    Use Cases/100k to compare countries of different sizes.
                </div>
            </div>
        </div>
    </div>

    <div class="footer">Data source: WHO Immunisation Database</div>
</body>
</html>
"""
    return html
