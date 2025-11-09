import sqlite3

DB_PATH = "ps_milestone_immunization_data.db"


def get_page_html(form_data=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM Vaccination;")
        total_vacc_rows = cur.fetchone()[0] or 0
    except Exception:
        total_vacc_rows = 0

    cur.execute("SELECT DISTINCT inf_type FROM InfectionData ORDER BY inf_type;")
    raw_diseases = [r[0] for r in cur.fetchall()]

    name_map = {
        "MEA": "Measles (MEA)",
        "PER": "Pertussis (PER)",
        "RUB": "Rubella (RUB)",
    }
    disease_list = [name_map.get(code, code) for code in raw_diseases]

    cur.execute("SELECT COALESCE(SUM(cases), 0) FROM InfectionData;")
    total_infections = cur.fetchone()[0] or 0

    conn.close()

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Vaccination Data Dashboard &ndash; Summary</title>
    <link rel="stylesheet" href="style.css">
    <style>
        body {{
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: #f2f2f2;
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
        .topnav a.active {{
            background-color: #111;
        }}
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
            background: rgba(2,36,73,0.45);
            color: #fff;
            padding: 24px 14px;
        }}
        .header-overlay h1 {{
            margin: 0;
            font-size: 20px;
        }}
        .header-overlay p {{
            margin: 4px 0 0 0;
            font-size: 12px;
        }}
        .content {{
            background: #e5e5e5;
            padding: 14px;
            min-height: 420px;
        }}
        .summary-row {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 14px;
        }}
        .tile {{
            background: #fff;
            border: 1px solid #d4d4d4;
            border-radius: 4px;
            padding: 10px 12px;
            flex: 1 1 220px;
        }}
        .tile h3 {{
            margin: 0 0 6px 0;
            font-size: 14px;
            color: #0d3b66;
        }}
        .tile ul {{
            margin: 0;
            padding-left: 20px;
            font-size: 12px;
        }}
        .big-number {{
            font-size: 26px;
            font-weight: bold;
        }}
        .section {{
            background: #fff;
            border: 1px solid #d4d4d4;
            border-radius: 4px;
            padding: 10px 12px;
            margin-bottom: 12px;
        }}
        .section h3 {{
            margin-top: 0;
            color: #0d3b66;
            font-size: 14px;
        }}
        .personas {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .persona-card {{
            background: #f9fafb;
            border: 1px solid #d4d4d4;
            border-radius: 4px;
            padding: 8px 10px;
            flex: 1 1 220px;
            font-size: 12px;
        }}
        .persona-card strong {{
            display: block;
            margin-bottom: 4px;
        }}
        table.team {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}
        table.team th, table.team td {{
            border: 1px solid #d4d4d4;
            padding: 4px 6px;
        }}
        table.team th {{
            background: #0d3b66;
            color: #fff;
            text-align: left;
        }}
        .footer {{
            background: #003866;
            color: #fff;
            text-align: center;
            padding: 10px 5px;
            font-size: 12px;
        }}
        @media (max-width: 900px) {{
            .summary-row {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="topnav">
        <a href="/">Home</a>
        <a href="/level2a">Explore</a>
        <a href="/level3a">Deep Dive</a>
        <a class="active" href="/level1b">Summary</a>
        <a href="/level2b">Compare</a>
        <a href="/level3b">Insights</a>
    </div>

    <div class="header-image">
        <div class="header-overlay">
            <h1>Vaccination Data Dashboard</h1>
            <p>Alternate view: overview, personas, and team.</p>
        </div>
    </div>

    <div class="content">
        <div class="summary-row">
            <div class="tile">
                <h3>Total vaccinations (rows)</h3>
                <p class="big-number">{total_vacc_rows}</p>
            </div>

            <div class="tile">
                <h3>Diseases in dataset</h3>
                <ul>
    """
    for d in disease_list:
        html += f"<li>{d}</li>"
    if not disease_list:
        html += "<li>None found</li>"

    html += f"""
                </ul>
            </div>

            <div class="tile">
                <h3>Total infections (all years)</h3>
                <p class="big-number">{int(total_infections):,}</p>
            </div>
        </div>

        <div class="section">
            <h3>Mission statement</h3>
            <p>
                This view gives a fast summary of what is inside the immunisation database so users
                know which diseases and tables are available before diving deeper.
            </p>
        </div>

        <div class="section">
            <h3>How to use</h3>
            <ul>
                <li>Start from this page to see what the database contains.</li>
                <li>Move to <strong>Explore</strong> to filter by antigen, infection and year.</li>
                <li>Use <strong>Deep Dive</strong> for improvement trends.</li>
            </ul>
        </div>

        <div class="section">
            <h3>Personas</h3>
            <div class="personas">
                <div class="persona-card">
                    <strong>Kris Nissen (s4183723)</strong>
                    University student<br>
                    Goals: show clean vaccination / infection insights.<br>
                    Needs: clear tables, filters that work, friendly layout.
                </div>
                <div class="persona-card">
                    <strong>Albin Binu (s4132293)</strong>
                    University student<br>
                    Goals: compare countries quickly.<br>
                    Needs: dropdowns, tidy summary and footer credit.
                </div>
            </div>
        </div>

        <div class="section">
            <h3>Team</h3>
            <table class="team">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Student ID</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Kris Nissen</td><td>s4183723</td></tr>
                    <tr><td>Albin Binu</td><td>s4132293</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="footer">
        Data source: WHO Immunisation Database
    </div>
</body>
</html>
"""
    return html
