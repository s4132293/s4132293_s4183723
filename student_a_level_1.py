import sqlite3

DB_NAME = "ps_milestone_immunization_data.db"

def get_page_html(params=None):
    if params is None:
        params = {}

    selected_disease = params.get("disease", ["ALL"])[0]

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT id, description FROM Infection_Type ORDER BY description;")
    disease_rows = cur.fetchall()

    cur.execute("SELECT MIN(YearID), MAX(YearID) FROM YearDate;")
    min_year, max_year = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM Vaccination;")
    total_vaccines = cur.fetchone()[0]

    cur.execute("PRAGMA table_info(InfectionData);")
    cols = [row[1] for row in cur.fetchall()]
    possible_case_cols = ["total_cases", "TotalCases", "cases", "Cases", "reported_cases"]
    case_col = None
    for c in possible_case_cols:
        if c in cols:
            case_col = c
            break

    if case_col:
        if selected_disease != "ALL":
            cur.execute(f"""
                SELECT COALESCE(SUM({case_col}), 0)
                FROM InfectionData
                WHERE inf_type = ?;
            """, (selected_disease,))
        else:
            cur.execute(f"SELECT COALESCE(SUM({case_col}), 0) FROM InfectionData;")
        total_cases = cur.fetchone()[0]
    else:
        total_cases = 0

    conn.close()

    disease_options_html = '<option value="ALL">All diseases</option>'
    for d_id, d_desc in disease_rows:
        selected_attr = " selected" if d_id == selected_disease else ""
        disease_options_html += f'<option value="{d_id}"{selected_attr}>{d_desc} ({d_id})</option>'

    if selected_disease == "ALL":
        diseases_label = ", ".join([f"{d[1]} ({d[0]})" for d in disease_rows])
    else:
        match = [d for d in disease_rows if d[0] == selected_disease]
        diseases_label = f"{match[0][1]} ({match[0][0]})" if match else selected_disease

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Vaccination Data Dashboard</title>
        <link rel="stylesheet" href="/style.css">
        <style>
            .icon {{
                font-size: 1.8em;
                color: #007acc;
            }}
            .about-box {{
                background-color: #e9f2fb;
                border-radius: 10px;
                border: 1px solid #b6d4f0;
                padding: 20px 40px;
                margin: 25px auto 0;
                max-width: 900px;
                text-align: center;
                color: #222;
                font-family: Arial, sans-serif;
                line-height: 1.6;
            }}
            .about-box h3 {{
                font-size: 1.4em;
                margin-bottom: 10px;
                color: #004b91;
                font-weight: normal;
            }}
            .about-box p {{
                font-size: 1em;
                font-weight: normal;
                margin: 0 auto;
                max-width: 700px;
            }}
        </style>
    </head>
    <body>
        <div class="topnav">
            <a class="active" href="/">Home</a>
            <a href="/level2a">Explore</a>
            <a href="/level3a">Deep Dive</a>
            <a href="/level1b">Summary</a>
            <a href="/level2b">Compare</a>
            <a href="/level3b">Insights</a>
        </div>

        <div class="hero-banner">
            <div class="hero-overlay">
                <h1>Vaccination Data Dashboard</h1>
                <p>Quick view of dataset coverage, years, and reported infection cases.</p>
            </div>
        </div>

        <div class="content">
            <form method="get" class="filter-row">
                <label for="disease">Disease / infection type:</label>
                <select name="disease" id="disease">
                    {disease_options_html}
                </select>
                <button type="submit">Update</button>
            </form>

            <table class="data-table">
                <tr><th>Timeframe covered</th><td>{min_year} &ndash; {max_year}</td></tr>
                <tr><th>Total vaccines (rows)</th><td>{total_vaccines:,}</td></tr>
                <tr><th>Total reported cases</th><td>{int(total_cases):,}</td></tr>
                <tr><th>Diseases represented</th><td>{diseases_label}</td></tr>
            </table>

            <!-- HOW TO USE SECTION -->
            <div class="how-to">
                <h3><span class="icon">💡</span> How to Use This Dashboard</h3>
                <div class="steps">
                    <div class="step">
                        <span class="icon">①</span>
                        <p>Select a disease or infection type from the dropdown menu.</p>
                    </div>
                    <div class="step">
                        <span class="icon">②</span>
                        <p>Click the Update button to view related vaccination data.</p>
                    </div>
                    <div class="step">
                        <span class="icon">③</span>
                        <p>Explore other pages using the navigation bar to deep dive into trends and country-level analysis.</p>
                    </div>
                </div>
            </div>

            <!-- ABOUT US SECTION -->
            <div class="about-box">
                <h3>About Us</h3>
                <p>
                    This project was developed by Kris Nissen (s4183723) and Albin Binu (s4132293)
                    as part of our university coursework. The website showcases our database design
                    and data analysis work using the WHO Immunisation Dataset, focusing on vaccination
                    coverage and infection trends worldwide. As university students, we wanted to make
                    the data more interactive and easy to explore through a simple dashboard interface.
                    Our goal was to combine the technical aspects of SQL, data querying, and visualization
                    into a user-friendly format that demonstrates how databases can help reveal meaningful
                    health insights.
                </p>
            </div>
        </div>

        <!-- FOOTER -->
        <footer class="footer">
            <p>Data source: WHO Immunisation Database</p>
        </footer>

    </body>
    </html>
    """
    return html
