from flask import Flask, render_template, request
import sqlite3

DB_PATH = "data.db"   # <- change if your file name differs
app = Flask(__name__)

def q(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]

@app.route("/")
def home_redirect():
    # Wireframe "Home" = Level 1B dashboard/mission
    return level1b()

# -----------------------
# Level 1B (Home / Mission + Dashboard tiles + Personas/Team)
# -----------------------
@app.route("/level1b")
def level1b():
    # Mission & how-to text
    mission = (
        "Our mission is to make global infection and vaccination data accessible and useful for "
        "students and analysts. Explore trends by year, infection type and economy to support evidence-based decisions."
    )
    how_to_use = [
        "Use the Explore Data page to filter by economy, infection type, and year.",
        "Above Average shows countries exceeding the global rate for a selected year/type.",
        "Personas and Team are stored in the database and rendered dynamically (Level 1B requirement)."
    ]

    # Dashboard tiles (per wireframe): Total Vaccinations, Disease List, Total Infections
    total_vacc = q("""
        SELECT ROUND(SUM(COALESCE(doses,0))) AS total_doses
        FROM Vaccination;
    """)[0]["total_doses"]

    disease_list = [r["description"] for r in q("""
        SELECT description FROM Infection_Type ORDER BY description;
    """)]

    total_infections = q("""
        SELECT ROUND(SUM(COALESCE(cases,0))) AS total_cases
        FROM InfectionData;
    """)[0]["total_cases"]

    # Personas & Team (Level 1B)
    personas = q("SELECT name, role, organisation, goals, needs FROM Persona ORDER BY id;")
    team = q("SELECT full_name, student_id FROM TeamMember ORDER BY id;")

    return render_template(
        "level1b.html",
        mission=mission,
        how_to_use=how_to_use,
        total_vacc=total_vacc,
        disease_list=disease_list,
        total_infections=total_infections,
        personas=personas,
        team=team
    )

# Helpers for dropdowns (reused in 2B & 3B)
def get_years():
    return [r["YearID"] for r in q("SELECT YearID FROM YearDate ORDER BY YearID;")]

def get_infection_types():
    return q("SELECT id AS code, description FROM Infection_Type ORDER BY description;")

def get_economies():
    return q("SELECT economyID, phase FROM Economy ORDER BY economyID;")

# -----------------------
# Level 2B (Explore Data: by Economic Status)
# -----------------------
@app.route("/level2b")
def level2b():
    years = get_years()
    inf_types = get_infection_types()
    economies = get_economies()

    year = int(request.args.get("year", years[-1] if years else 2020))
    inf_code = request.args.get("infection", inf_types[0]["code"] if inf_types else "MEA")
    econ_id = int(request.args.get("economy", economies[0]["economyID"] if economies else 1))

    # Country table (cases per 100k)
    sql_countries = """
    SELECT it.description AS infection,
           :year         AS year,
           c.name        AS country,
           e.phase       AS economic_phase,
           COALESCE(id.cases, 0.0) AS cases,
           cp.population,
           CASE WHEN cp.population IS NOT NULL AND cp.population > 0
                THEN ROUND(id.cases * 100000.0 / cp.population, 2)
                ELSE NULL
           END AS cases_per_100k
    FROM Country c
    JOIN Economy e ON e.economyID = c.economy
    JOIN Infection_Type it ON it.id = :inf
    LEFT JOIN InfectionData id
           ON id.country = c.CountryID AND id.year = :year AND id.inf_type = it.id
    LEFT JOIN CountryPopulation cp
           ON cp.country = c.CountryID AND cp.year = :year
    WHERE e.economyID = :econ
    ORDER BY cases_per_100k DESC NULLS LAST, country;
    """
    rows_countries = q(sql_countries, {"inf": inf_code, "year": year, "econ": econ_id})

    # Summary (by economy)
    sql_summary = """
    SELECT e.phase AS economic_phase,
           :year  AS year,
           ROUND(SUM(COALESCE(id.cases,0)), 0) AS total_cases
    FROM Economy e
    JOIN Country c ON c.economy = e.economyID
    LEFT JOIN InfectionData id
           ON id.country = c.CountryID AND id.year = :year AND id.inf_type = :inf
    GROUP BY e.phase
    ORDER BY e.phase;
    """
    rows_summary = q(sql_summary, {"inf": inf_code, "year": year})

    return render_template(
        "level2b.html",
        years=years, inf_types=inf_types, economies=economies,
        sel_year=year, sel_inf=inf_code, sel_econ=econ_id,
        rows_countries=rows_countries, rows_summary=rows_summary
    )

# -----------------------
# Level 3B (Above-Average countries)
# -----------------------
@app.route("/level3b")
def level3b():
    years = get_years()
    inf_types = get_infection_types()

    year = int(request.args.get("year", years[-1] if years else 2020))
    inf_code = request.args.get("infection", inf_types[0]["code"] if inf_types else "MEA")

    # Global rate / 100k
    global_rate = q("""
    WITH agg AS (
      SELECT SUM(COALESCE(id.cases,0)) AS total_cases,
             SUM(COALESCE(cp.population,0)) AS total_pop
      FROM Country c
      LEFT JOIN InfectionData id
             ON id.country = c.CountryID AND id.year = :year AND id.inf_type = :inf
      LEFT JOIN CountryPopulation cp
             ON cp.country = c.CountryID AND cp.year = :year
    )
    SELECT CASE WHEN total_pop > 0
           THEN ROUND(total_cases * 100000.0 / total_pop, 2)
           ELSE NULL END AS global_rate_100k
    FROM agg;
    """, {"year": year, "inf": inf_code})[0]["global_rate_100k"]

    rows = q("""
    SELECT c.name AS country,
           it.description AS infection,
           :year AS year,
           ROUND(id.cases * 100000.0 / cp.population, 2) AS rate_100k
    FROM Country c
    JOIN Infection_Type it ON it.id = :inf
    JOIN InfectionData id
         ON id.country = c.CountryID AND id.year = :year AND id.inf_type = it.id
    JOIN CountryPopulation cp
         ON cp.country = c.CountryID AND cp.year = :year
    WHERE cp.population > 0
      AND id.cases IS NOT NULL
      AND (id.cases * 100000.0 / cp.population) > :gr
    ORDER BY rate_100k DESC;
    """, {"year": year, "inf": inf_code, "gr": (global_rate if global_rate is not None else -1)})

    return render_template(
        "level3b.html",
        years=years, inf_types=inf_types,
        sel_year=year, sel_inf=inf_code,
        global_rate=global_rate, rows=rows
    )

if __name__ == "__main__":
    app.run(debug=True)