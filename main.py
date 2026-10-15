import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import time
import hashlib
import hmac
import extra_streamlit_components as stx




# --------------------------------------------------
# PASSWORD PROTECTION — 8-HOUR COOKIE SESSION
# --------------------------------------------------

SESSION_DURATION = 8 * 60 * 60
COOKIE_NAME = "elgin_auth"

# Local development uses HTTP.
# Change to True when deployed on HTTPS.
COOKIE_SECURE = False

if "cookie_manager" not in st.session_state:
    st.session_state["cookie_manager"] = stx.CookieManager(
        key="elgin_auth_cookie_manager"
    )

cookie_manager = st.session_state["cookie_manager"]


def create_auth_token():
    expiry = int(time.time()) + SESSION_DURATION
    signing_key = st.secrets["cookie_signing_key"]

    signature = hmac.new(
        signing_key.encode("utf-8"),
        str(expiry).encode("utf-8"),
        digestmod="sha256"
    ).hexdigest()

    return f"{expiry}.{signature}"


def valid_auth_token(token):
    if not isinstance(token, str):
        return False

    try:
        expiry_text, supplied_signature = token.split(".", 1)
        expiry = int(expiry_text)

        if expiry <= time.time():
            return False

        signing_key = st.secrets["cookie_signing_key"]

        expected_signature = hmac.new(
            signing_key.encode("utf-8"),
            expiry_text.encode("utf-8"),
            digestmod="sha256"
        ).hexdigest()

        return hmac.compare_digest(
            supplied_signature,
            expected_signature
        )

    except (ValueError, TypeError):
        return False


def check_password():
    # Keep a successful login for the current Streamlit session
    if st.session_state.get("logged_in", False):
        return True

    cookies = cookie_manager.get_all(key="read_auth_cookies")
    token = cookies.get(COOKIE_NAME) if cookies else None

    if valid_auth_token(token):
        st.session_state["logged_in"] = True
        return True

    st.title("Elgin City FC")
    st.subheader("Scouting Dashboard")

    with st.form("login_form"):
        password = st.text_input(
            "Enter password",
            type="password"
        )
        submitted = st.form_submit_button("Log in")

    if submitted:
        if hmac.compare_digest(
            password,
            st.secrets["app_password"]
        ):
            st.session_state["logged_in"] = True

            cookie_manager.set(
                COOKIE_NAME,
                create_auth_token(),
                key="set_auth_cookie",
                path="/",
                max_age=SESSION_DURATION,
                secure=COOKIE_SECURE,
                same_site="lax"
            )

            return True

        st.error("Incorrect password")

    return False


if not check_password():
    st.stop()

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Elgin City",
    layout="wide"
)

# --------------------------------------------------
# ELGIN CITY BRANDING AND STYLING
# --------------------------------------------------

st.logo(
    "assets/elgin_badge.png",
    size="large"
)

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #FFFFFF;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #171717;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF;
    }

    /* Main headings */
    h1, h2, h3 {
        color: #171717;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #D0D0D0;
        border-left: 5px solid #C8A64B;
        padding: 16px;
        border-radius: 8px;
    }

    /* Metric labels */
    [data-testid="stMetricLabel"] {
        color: #555555;
    }

    /* Metric values */
    [data-testid="stMetricValue"] {
        color: #171717;
    }

    /* Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #D0D0D0;
        border-radius: 8px;
    }

    /* Buttons */
    .stButton > button {
        border: 1px solid #C8A64B;
        border-radius: 6px;
    }

    .stButton > button:hover {
        background-color: #C8A64B;
        color: #171717;
        border-color: #C8A64B;
    }
    .block-container {
    padding-top: 5rem !important;
    padding-bottom: 1rem !important;
}

[data-testid="stVerticalBlock"] {
    gap: 0.75rem;
}

h1 {
    margin-top: 0.25rem;
    padding-top: 0rem;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# PROJECT PATHS AND DATA
# --------------------------------------------------

DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")

scores = pd.read_csv(DATA_DIR / "z_score_all.csv")
players = pd.read_csv(DATA_DIR / "all_leagues.csv")

def open_player_profile(player_name, team=None, season=None):
    st.session_state["profile_player_to_open"] = str(player_name)

    if team is not None:
        st.session_state["profile_team_to_open"] = str(team)

    if season is not None:
        st.session_state["profile_season_to_open"] = str(season)

    st.session_state["pending_navigation"] = "Player Profiles"

# --------------------------------------------------
# POSITION-SPECIFIC SCATTER PLOT METRICS
# --------------------------------------------------

SCATTER_METRICS = {
    "FB": {
        "attacking": {
            "x": "Crosses_p90",
            "y": "xA_p90",
            "x_label": "Crosses per 90",
            "y_label": "Expected Assists per 90",
            "title": "Crossing & Chance Creation",
        },
        "defending": {
            "x": "Defensive_duels_p90",
            "y": "Defensive_duels_won_pct",
            "x_label": "Defensive Duels per 90",
            "y_label": "Defensive Duel Win %",
            "title": "Defensive Duels",
        },
    },

    "CB": {
        "attacking": {
            "x": "Progressive_passes_p90",
            "y": "Accurate_passes_pct",
            "x_label": "Progressive Passes per 90",
            "y_label": "Pass Accuracy %",
            "title": "Passing & Progression",
        },
        "defending": {
            "x": "Defensive_duels_p90",
            "y": "Defensive_duels_won_pct",
            "x_label": "Defensive Duels per 90",
            "y_label": "Defensive Duel Win %",
            "title": "Defensive Duels",
        },
    },

    "DM": {
        "attacking": {
            "x": "Progressive_passes_p90",
            "y": "Forward_passes_p90",
            "x_label": "Progressive Passes per 90",
            "y_label": "Forward Passes per 90",
            "title": "Passing & Progression",
        },
        "defending": {
            "x": "PAdj_Interceptions",
            "y": "Successful_defensive_actions_p90",
            "x_label": "Possession-Adjusted Interceptions",
            "y_label": "Successful Defensive Actions per 90",
            "title": "Interceptions & Defensive Actions",
        },
    },

    "CM": {
        "attacking": {
            "x": "Progressive_passes_p90",
            "y": "xA_p90",
            "x_label": "Progressive Passes per 90",
            "y_label": "Expected Assists per 90",
            "title": "Progression & Chance Creation",
        },
        "defending": {
            "x": "Successful_defensive_actions_p90",
            "y": "PAdj_Interceptions",
            "x_label": "Successful Defensive Actions per 90",
            "y_label": "Possession-Adjusted Interceptions",
            "title": "Defensive Actions & Interceptions",
        },
    },

    "AM": {
        "attacking": {
            "x": "Key_passes_p90",
            "y": "xA_p90",
            "x_label": "Key Passes per 90",
            "y_label": "Expected Assists per 90",
            "title": "Chance Creation",
        },
        "defending": {
            "x": "Successful_defensive_actions_p90",
            "y": "Defensive_duels_won_pct",
            "x_label": "Successful Defensive Actions per 90",
            "y_label": "Defensive Duel Win %",
            "title": "Defensive Contribution",
        },
    },

    "WG": {
        "attacking": {
            "x": "Dribbles_p90",
            "y": "xA_p90",
            "x_label": "Dribbles per 90",
            "y_label": "Expected Assists per 90",
            "title": "Dribbling & Chance Creation",
        },
        "defending": {
            "x": "Successful_defensive_actions_p90",
            "y": "Defensive_duels_won_pct",
            "x_label": "Successful Defensive Actions per 90",
            "y_label": "Defensive Duel Win %",
            "title": "Defensive Contribution",
        },
    },

    "CF": {
        "attacking": {
            "x": "xG_p90",
            "y": "Goals_p90",
            "x_label": "Expected Goals per 90",
            "y_label": "Goals per 90",
            "title": "Expected Goals & Goals",
        },
        "defending": {
            "x": "Offensive_duels_p90",
            "y": "Aerial_duels_won_pct",
            "x_label": "Offensive Duels per 90",
            "y_label": "Aerial Duel Win %",
            "title": "Duels & Aerial Ability",
        },
    },
}
ROLE_METRICS = {
    "FB": [
        "Goals", "xG_p90", "xA_p90",
        "Accurate_crosses_pct", "Successful_dribbles_pct",
        "Accurate_passes_pct", "Accurate_progressive_passes_pct",
        "Progressive_passes_p90", "Accurate_progressive_passes_pct",
        "Defensive_duels_p90", "Successful_defensive_actions_p90",
        "PAdj_Interceptions", "Defensive_duels_won_pct",
        "Aerial_duels_won_pct",
    ],
    "CB": [
        "Goals", "Accurate_passes_pct",
        "Accurate_progressive_passes_pct", "Progressive_passes_p90",
        "Successful_attacking_actions_p90", "PAdj_Sliding_tackles",
        "Successful_attacking_actions_p90", "Successful_defensive_actions_p90",
        "Offensive_duels_p90", "PAdj_Interceptions",
        "Defensive_duels_won_pct", "Defensive_duels_p90",
        "Aerial_duels_won_pct", "Aerial_duels_p90",
    ],
    "DM": [
        "Goals", "xG_p90", "Assists", "xA_p90",
        "Successful_attacking_actions_p90", "Passes_p90",
        "Accurate_passes_pct", "Accurate_progressive_passes_pct",
        "Progressive_passes_p90", "Forward_passes_p90",
        "Lateral_passes_p90", "Defensive_duels_won_pct",
        "Successful_defensive_actions_p90", "Offensive_duels_p90",
        "PAdj_Interceptions", "Aerial_duels_won_pct",
    ],
    "CM": [
        "Goals", "Assists", "xA_p90",
        "Successful_attacking_actions_p90", "Key_passes_p90",
        "Accurate_passes_pct", "Accurate_progressive_passes_pct",
        "Progressive_passes_p90", "Progressive_runs_p90",
        "Passes_p90", "Successful_defensive_actions_p90",
        "Offensive_duels_p90", "PAdj_Interceptions",
        "Aerial_duels_won_pct",
    ],
    "AM": [
        "Goals", "xG_p90", "Assists", "xA_p90",
        "Successful_attacking_actions_p90", "Key_passes_p90",
        "Deep_completions_p90", "Accurate_passes_pct",
        "Progressive_passes_p90", "Passes_p90",
        "Successful_dribbles_pct", "Dribbles_p90",
        "Successful_defensive_actions_p90",
    ],
    "WG": [
        "Goals_p90", "xG_p90", "Assists", "xA_p90",
        "Key_passes_p90", "Goal_conversion_pct",
        "Deep_completions_p90", "Accurate_crosses_pct",
        "Crosses_p90", "Successful_attacking_actions_p90",
        "Successful_dribbles_pct", "Dribbles_p90",
        "Successful_defensive_actions_p90",
    ],
    "CF": [
        "Goals", "xG_p90", "Shots_on_target_pct",
        "Successful_attacking_actions_p90", "Touches_in_box_p90",
        "Assists", "xA_p90", "Key_passes_p90",
        "Offensive_duels_p90", "Defensive_duels_won_pct",
        "Aerial_duels_won_pct", "Successful_defensive_actions_p90",
        "Goal_conversion_pct", "Successful_attacking_actions_p90",
    ],
}

POSITION_GROUPS = {
    "FB": {
        "positions": ["RB", "LB", "RWB", "LWB"],
        "title": "Full Back Profile",
    },
    "CB": {
        "positions": ["CB"],
        "title": "Centre Back Profile",
    },
    "DM": {
        "positions": ["DM"],
        "title": "Defensive Midfielder Profile",
    },
    "CM": {
        "positions": ["CM"],
        "title": "Centre Midfielder Profile",
    },
    "AM": {
        "positions": ["AM"],
        "title": "Attacking Midfielder Profile",
    },
    "WG": {
        "positions": ["LW", "RW"],
        "title": "Winger Profile",
    },
    "CF": {
        "positions": ["CF"],
        "title": "Centre Forward Profile",
    },
}

# Clear table selections before those widgets are created
if st.session_state.pop("clear_player_table_selection", False):
    for selection_key in [
        "home_player_table",
        "recruitment_player_table",
    ]:
        st.session_state.pop(selection_key, None)

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.markdown("""
<style>
/* SIDEBAR BACKGROUND */
[data-testid="stSidebar"] {
    background-color: #171717;
    min-width: 260px;
    max-width: 260px;
}

/* Overall sidebar spacing */
[data-testid="stSidebar"] > div:first-child {
    padding: 5.5rem 1rem 1rem 1rem;
}

/* CLUB TITLE */
[data-testid="stSidebar"] h1 {
    color: #FFFFFF;
    font-size: 1.3rem;
    font-weight: 700;
    margin: 0 0 0.15rem 0;
    padding: 0;
}

/* PLAYER RECRUITMENT SUBTITLE */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #999999;
    font-size: 0.72rem;
    letter-spacing: 1px;
    margin-top: 0;
    margin-bottom: 0.7rem;
    padding: 0;
}

/* GOLD DIVIDER UNDER CLUB HEADING */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]::after {
    content: "";
    display: block;
    height: 2px;
    background-color: #C8A64B;
    width: 100%;
    margin-top: 0.9rem;
}

/* NAVIGATION HEADING */
[data-testid="stSidebar"] .stRadio > label {
    color: #999999;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-top: 0.7rem;
    margin-bottom: 0.6rem;
}

/* SPACE BETWEEN NAVIGATION ITEMS */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] {
    gap: 0.35rem;
}


/* NAVIGATION ITEMS — EQUAL WIDTH AND HEIGHT */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
    display: flex !important;
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    height: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
    box-sizing: border-box !important;
    align-items: center !important;
    padding: 0 0.8rem !important;
    margin: 0 !important;
    background: #222222;
    border: 1px solid #333333;
    border-left: 3px solid transparent;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.15s ease;
}


/* REMOVE RADIO CIRCLES */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label > div:first-child {
    display: none !important;
}

[data-testid="stSidebar"] .stRadio [role="radiogroup"] input[type="radio"] {
    display: none !important;
}

/* NAVIGATION TEXT */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label p {
    color: #DDDDDD !important;
    font-size: 0.88rem;
    font-weight: 500;
    margin: 0;
}

/* HOVER EFFECT */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
    background: #303030;
    border-color: #555555;
    border-left-color: #C8A64B;
}

/* SELECTED PAGE — GOLD HIGHLIGHT */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) {
    background: #C8A64B;
    border-color: #C8A64B;
    border-left-color: #FFFFFF;
}

/* SELECTED PAGE TEXT */
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:has(input:checked) p {
    color: #171717 !important;
    font-weight: 700;
}

/* Completely hide radio circles and their wrappers */
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"],
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child,
[data-testid="stSidebar"] [data-testid="stRadio"] label > div > div:first-child {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Prevent empty space where circles used to be */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    gap: 0 !important;
}

/* Centre and enlarge the Elgin City logo */
[data-testid="stSidebar"] img {
    display: block !important;
    width: 75px !important;
    max-width: 75px !important;
    height: auto !important;
    margin: 0 auto 1.2rem auto !important;
    object-fit: contain;
}

/* FORCE ALL NAVIGATION BOXES TO MATCH */
[data-testid="stSidebar"] [data-testid="stRadio"] {
    width: 100% !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    width: 100% !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    width: 100% !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] > label {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    flex: 0 0 48px !important;
    height: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
    box-sizing: border-box !important;
    align-self: stretch !important;
}

</style>
""", unsafe_allow_html=True)

st.sidebar.title("ELGIN CITY FC")
st.sidebar.caption("PLAYER RECRUITMENT")

    # Handle a clicked player profile link
if "profile_player" in st.query_params:
    st.session_state["profile_player_to_open"] = (
        st.query_params.get("profile_player")
    )
    st.session_state["profile_team_to_open"] = (
        st.query_params.get("profile_team")
    )
    st.session_state["profile_season_to_open"] = (
        st.query_params.get("profile_season")
    )
    st.session_state["pending_navigation"] = "Player Profiles"
    st.query_params.clear()

# Apply requested navigation before creating the sidebar widget
if "pending_navigation" in st.session_state:
    st.session_state["page_navigation"] = (
        st.session_state.pop("pending_navigation")
    )

page = st.sidebar.radio(
    "Menu",
    [
        "Home",
        "Scoring Framework",
        "Squad Report",
        "Recruitment Focus",
        "Player Profiles",
        "Player Comparison"
    ],
    key="page_navigation",
    label_visibility="visible"
)

# --------------------------------------------------
# HOME — PLAYER DATABASE
# --------------------------------------------------

if page == "Home":

    st.title("Player Database")

    # Cascading filters
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        leagues = ["All"] + sorted(
            players["League"].dropna().unique().tolist()
        )

        selected_league = st.selectbox(
            "League",
            leagues
        )

    # Apply league filter
    filtered_players = players.copy()

    if selected_league != "All":
        filtered_players = filtered_players[
            filtered_players["League"] == selected_league
        ]

    with col2:
        seasons = ["All"] + sorted(
            filtered_players["Year"].dropna().unique().tolist()
        )

        selected_year = st.selectbox(
            "Season",
            seasons
        )

    # Apply season filter
    if selected_year != "All":
        filtered_players = filtered_players[
            filtered_players["Year"] == selected_year
        ]

    with col3:
        teams = ["All"] + sorted(
            filtered_players["Team"].dropna().unique().tolist()
        )

        selected_team = st.selectbox(
            "Team",
            teams
        )

    # Apply team filter
    if selected_team != "All":
        filtered_players = filtered_players[
            filtered_players["Team"] == selected_team
        ]

    with col4:
        positions = ["All"] + sorted(
            filtered_players["Position"].dropna().unique().tolist()
        )

        selected_position = st.selectbox(
            "Position",
            positions
        )

    # Apply position filter
    if selected_position != "All":
        filtered_players = filtered_players[
            filtered_players["Position"] == selected_position
        ]

    with col5:
        min_age = int(players["Age"].min())
        max_age = int(players["Age"].max())

        age_range = st.slider(
            "Age range",
            min_value=min_age,
            max_value=max_age,
            value=(min_age, max_age)
        )

    # Apply age filter
    filtered_players = filtered_players[
        filtered_players["Age"].between(
            age_range[0],
            age_range[1]
        )
    ]

    # Player count
    st.write(
        f"Players matching filters: {len(filtered_players):,}"
    )

    # Select displayed columns
    default_columns = [
        "Player",
        "Team",
        "League",
        "Year",
        "Position",
        "Age",
        "Minutes_played",
        "Goals",
        "Assists"
    ]

    default_columns = [
        col for col in default_columns
        if col in filtered_players.columns
    ]

    selected_columns = st.multiselect(
        "Columns to display",
        options=players.columns.tolist(),
        default=default_columns
    )


    # Player table with clickable player names
    display_data = filtered_players[selected_columns].copy()

    display_data["Player"] = filtered_players.apply(
        lambda row: (
            f"?profile_player={row['Player']}"
            f"&profile_team={row['Team']}"
            f"&profile_season={row['Year']}"
        ),
        axis=1
    )

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Player": st.column_config.LinkColumn(
                "Player",
                display_text=r"\?profile_player=(.*?)&profile_team="
            )
        }
    )


    # Summary tiles
    tile1, tile2, tile3, tile4, tile5 = st.columns(5)

    with tile1:
        st.metric(
            "Players",
            f"{len(filtered_players):,}"
        )

    with tile2:
        st.metric(
            "Leagues",
            f"{filtered_players['League'].nunique():,}"
        )

    with tile3:
        st.metric(
            "Teams",
            f"{filtered_players['Team'].nunique():,}"
        )

    with tile4:
        average_age = filtered_players["Age"].mean()

        st.metric(
            "Average Age",
            f"{average_age:.1f}"
            if pd.notna(average_age) else "N/A"
        )

    with tile5:
        average_minutes = filtered_players["Minutes_played"].mean()

        st.metric(
            "Average Minutes",
            f"{average_minutes:,.0f}"
            if pd.notna(average_minutes) else "N/A"
        )

# --------------------------------------------------
# SCORING FRAMEWORK
# --------------------------------------------------

elif page == "Scoring Framework":

    st.title("Scoring Framework")

    st.markdown(
        "Position-specific scores combine weighted performance metrics. "
        "Each position uses a different set of indicators."
    )

    framework = {
        "Full Backs": [
            "Duels Won %",
            "Crosses p90",
            "Accurate Crosses %",
            "Aerial Duels Won %",
            "Expected Assists (xA) p90",
            "Successful Defensive Actions p90",
            "Progressive Runs p90",
            "Possession-Adjusted Interceptions"
        ],
        "Centre Backs": [
            "Aerial Duels Won %",
            "Duels Won %",
            "Possession-Adjusted Interceptions",
            "Progressive Passes p90",
            "Accurate Passes %",
            "Successful Defensive Actions p90",
            "Accurate Progressive Passes %"
        ],
        "Defensive Midfielders": [
            "Accurate Passes %",
            "Expected Assists (xA) p90",
            "Key Passes p90",
            "Progressive Runs p90",
            "Defensive Duels Won %",
            "Possession-Adjusted Interceptions",
            "Successful Defensive Actions p90",
            "Accurate Progressive Passes %",
            "Progressive Passes p90"
        ],
        "Attacking Midfielders": [
            "Goals p90",
            "Expected Goals (xG) p90",
            "Expected Assists (xA) p90",
            "Key Passes p90",
            "Passes to Penalty Area p90",
            "Successful Attacking Actions p90",
            "Dribbles p90",
            "Successful Dribbles %",
            "Accurate Through Passes %"
        ],
        "Wingers": [
            "Goals p90",
            "Expected Goals (xG) p90",
            "Expected Assists (xA) p90",
            "Dribbles p90",
            "Successful Dribbles %",
            "Successful Attacking Actions p90",
            "Crosses p90",
            "Accurate Crosses %",
            "Progressive Runs p90"
        ],
        "Centre Forwards": [
            "Goals p90",
            "Expected Goals (xG) p90",
            "Shots on Target %",
            "Touches in Box p90",
            "Successful Defensive Actions p90",
            "Aerial Duels Won %",
            "Expected Assists (xA) p90"
        ]
    }

    # Styling
    st.markdown("""
    <style>
        .framework-card {
            background: #FFFFFF;
            border: 1px solid #D0D0D0;
            border-left: 3px solid #C8A64B;
            border-radius: 4px;
            padding: 7px 8px;
            margin-bottom: 5px;
            min-height: 36px;
            display: flex;
            align-items: center;
            font-size: 13px;
            line-height: 1.3;
            color: #171717;
            overflow-wrap: anywhere;
        }

        .framework-heading {
            background: #171717;
            color: #C8A64B;
            padding: 9px 5px;
            border-radius: 4px;
            text-align: center;
            font-size: 13px;
            font-weight: 700;
            min-height: 46px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .framework-explanation {
            font-size: 16px;
            line-height: 1.6;
            color: #333333;
        }
    </style>
    """, unsafe_allow_html=True)

    # Position-specific metrics
    columns = st.columns(6, gap="small")

    for column, (position, metrics) in zip(columns, framework.items()):
        with column:
            st.markdown(
                f'<div class="framework-heading">{position}</div>',
                unsafe_allow_html=True
            )

            for metric in metrics:
                st.markdown(
                    f'<div class="framework-card">{metric}</div>',
                    unsafe_allow_html=True
                )

    # Scoring methodology
    st.divider()

    st.markdown("#### Scoring Methodology")

    st.markdown("""
    <div class="framework-explanation">
    Player scores are calculated from a weighted combination of position-specific performance metrics. The metrics used vary by position and are outlined below:
    <br><br>
    Players are rated using a combination of the metrics listed above, with each metric scored on how much they outperform or underperform the league average. The scores for each metric are then weighted in terms of importance and then combined to produce an overall position score.
    <br><br>
    Each player's season is compared against a combined Scottish League 1 and League 2 dataset covering 2023/24 to 2026/27. Scores are then converted to a 0–100 scale within each league and position, where 100 represents the highest-rated player in that league and position. For example, Calvin Miller’s 2024 Falkirk season is currently the highest-rated winger season in League 1, giving him a score of 100. As 2026/27 is still at an early stage with limited data, strong early performances may score unusually highly; these scores will become more balanced as more data is added.
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# SQUAD REPORT
# --------------------------------------------------

elif page == "Squad Report":

    import plotly.express as px
    import plotly.graph_objects as go

    st.title("Squad Report")

    # --------------------------------------------------
    # SELECTORS, POSITION CHART AND SUMMARY TILES
    # --------------------------------------------------

    selector_col, chart_col, tiles_col = st.columns(
    [1.15, 1.35, 2],
    gap="medium",
    vertical_alignment="center"
)

    # -------------------------
    # Team and season selectors
    # -------------------------

    with selector_col:

        teams = sorted(
            scores["Team"].dropna().unique().tolist()
        )

        default_index = (
            teams.index("Elgin City")
            if "Elgin City" in teams
            else 0
        )

        selected_team = st.selectbox(
            "Team",
            teams,
            index=default_index,
            key="squad_report_team"
        )

        team_data = scores[
            scores["Team"] == selected_team
        ].copy()

        seasons = sorted(
            team_data["Year"].dropna().unique().tolist(),
            key=str,
            reverse=True
        )

        if seasons:
            default_season_index = next(
                (
                    i for i, season in enumerate(seasons)
                    if str(season) == "2027"
                ),
                0
            )

            selected_season = st.selectbox(
                "Season",
                seasons,
                index=default_season_index,
                key="squad_report_season"
            )
        else:
            selected_season = None
            st.selectbox(
                "Season",
                ["No seasons available"],
                disabled=True,
                key="squad_report_no_season"
            )

    # -------------------------
    # Filter selected squad
    # -------------------------

    if selected_season is not None:
        squad = team_data[
            team_data["Year"] == selected_season
        ].copy()
    else:
        squad = team_data.iloc[0:0].copy()

    # -------------------------
    # Position distribution
    # -------------------------

    with chart_col:

        if not squad.empty:

            position_groups = {
    "GK": "GK",
    "RB": "FB",
    "LB": "FB",
    "RWB": "FB",
    "LWB": "FB",
    "CB": "CB",
    "CM": "CM",
    "DM": "CM",
    "AM": "AM",
    "LW": "WG",
    "RW": "WG",
    "CF": "CF"
}

            position_data = (
                squad["Position"]
                .fillna("")
                .str.strip()
                .str.upper()
            )

            grouped_positions = (
                position_data.map(position_groups)
                .fillna("Other")
            )

            position_order = [
                "FB", "CB", "CM", "AM", "WG", "CF", "GK", "Other"
            ]

            position_counts = (
                grouped_positions
                .value_counts()
                .reindex(position_order, fill_value=0)
            )

            position_counts = position_counts[
                position_counts > 0
            ]

            position_colours = {
    "GK": "#171717",
    "FB": "#C8A64B",
    "CB": "#2878B5",
    "CM": "#35A7A0",
    "AM": "#7357A6",
    "WG": "#E08B36",
    "CF": "#D65F59",
    "Other": "#929292"
}

            colours = [
                position_colours[position]
                for position in position_counts.index
            ]

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=position_counts.index.tolist(),
                        values=position_counts.values.tolist(),
                        hole=0.62,
                        sort=False,
                        direction="clockwise",
                        marker=dict(
                            colors=colours,
                            line=dict(
                                color="#FFFFFF",
                                width=1
                            )
                        ),
                        # Keep labels and player counts inside slices
                        text=[
                            f"{position}<br>{count}"
                            for position, count
                            in zip(
                                position_counts.index,
                                position_counts.values
                            )
                        ],
                        textinfo="text",
                        textposition="inside",
                        insidetextorientation="horizontal",
                        textfont=dict(
                            size=11,
                            color="#FFFFFF"
                        ),
                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "Players: %{value}<br>"
                            "Squad share: %{percent}"
                            "<extra></extra>"
                        )
                    )
                ]
            )

            fig.update_layout(
                height=280,
                autosize=True,
                margin=dict(l=5, r=5, t=5, b=5),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                uniformtext=dict(
                    minsize=9,
                    mode="hide"
                ),
                annotations=[
                    dict(
                        text=(
                            f"<b>{len(squad)}</b>"
                            "<br><span style='font-size:10px'>"
                            "SQUAD SIZE</span>"
                        ),
                        x=0.5,
                        y=0.5,
                        font=dict(
                            size=23,
                            color="#171717"
                        ),
                        showarrow=False
                    )
                ]
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False}
            )

        else:
            st.info("No players found for this team and season.")

        # -------------------------
    # Four summary tiles in a 2x2 grid
    # -------------------------

    with tiles_col:

        if not squad.empty:

            most_appearances = squad.loc[
                squad["Matches_played"].idxmax()
            ]

            top_scorer = squad.loc[
                squad["Goals"].fillna(0).idxmax()
            ]

            top_assister = squad.loc[
                squad["Assists"].fillna(0).idxmax()
            ]

            average_age = (
                f"{squad['Age'].mean():.1f}"
                if squad["Age"].notna().any()
                else "N/A"
            )

            def summary_tile(title, value, player=""):
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #D0D0D0;
                        border-left: 4px solid #C8A64B;
                        border-radius: 6px;
                        padding: 10px 12px;
                        height: 82px;
                        box-sizing: border-box;
                        background: #FFFFFF;
                        margin-bottom: 8px;
                        overflow: hidden;
                    ">
                        <div style="
                            font-size: 12px;
                            color: #555555;
                            margin-bottom: 4px;
                        ">{title}</div>
                        <div style="
                            font-size: 19px;
                            font-weight: 600;
                            color: #171717;
                            line-height: 1.2;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                        ">{value}</div>
                        <div style="
                            font-size: 11px;
                            color: #777777;
                            margin-top: 3px;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                        ">{player}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            row1 = st.columns(2, gap="small")

            with row1[0]:
                summary_tile("Average Age", average_age)

            with row1[1]:
                summary_tile(
                    "Most Appearances",
                    f"{most_appearances['Matches_played']:,.0f} apps",
                    most_appearances["Player"]
                )

            row2 = st.columns(2, gap="small")

            with row2[0]:
                summary_tile(
                    "Top Scorer",
                    f"{top_scorer['Goals']:g} goals",
                    top_scorer["Player"]
                )

            with row2[1]:
                summary_tile(
                    "Most Assists",
                    f"{top_assister['Assists']:g} assists",
                    top_assister["Player"]
                )

        else:
            st.info("No players found for this team and season.")
        # --------------------------------------------------
    # POSITIONAL RANKINGS
    # --------------------------------------------------

    st.divider()

    if not squad.empty:

        st.subheader(
            f"{selected_team} | {selected_season} — Positional Rankings"
        )

        position_tables = [
            {
                "title": "Full Backs",
                "score": "FB Score",
                "positions": ["RB", "LB", "RWB", "LWB"],
                "colour": "#C8A64B"
            },
            {
                "title": "Centre Backs",
                "score": "CB Score",
                "positions": ["CB"],
                "colour": "#2878B5"
            },
            {
                "title": "Centre Midfielders",
                "score": "DLP Score",
                "positions": ["CM", "DM"],
                "colour": "#35A7A0"
            },
            {
                "title": "Attacking Midfielders",
                "score": "AP Score",
                "positions": ["AM"],
                "colour": "#7357A6"
            },
            {
                "title": "Wingers",
                "score": "WG Score",
                "positions": ["LW", "RW"],
                "colour": "#E08B36"
            },
            {
                "title": "Centre Forwards",
                "score": "CF Score",
                "positions": ["CF"],
                "colour": "#D65F59"
            }
        ]

        for row_start in range(0, len(position_tables), 3):

            cols = st.columns(3, gap="medium")

            for col, role in zip(
                cols,
                position_tables[row_start:row_start + 3]
            ):

                with col:

                    st.markdown(
                        f"""
                        <div style="
                            border-bottom: 3px solid {role['colour']};
                            padding-bottom: 6px;
                            margin-bottom: 8px;
                        ">
                            <strong>{role['title']}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Select players with a score for this role
                    role_data = squad[
    squad["Position"].fillna("").str.strip().str.upper().isin(
        role["positions"]
    )
    & squad[role["score"]].notna()
].copy()

                    # Sort by the existing score, highest first
                    role_data = role_data.sort_values(
                        role["score"],
                        ascending=False
                    )

                    if role_data.empty:

                        st.caption("No scored players")

                    else:

                        role_data["Score"] = role_data[
                            role["score"]
                        ].round(1)

                        role_display = role_data[
                            [
                                "Player",
                                "Age",
                                "Position",
                                "Score"
                            ]
                        ].rename(
                            columns={
                                "Player": "Player",
                                "Age": "Age",
                                "Position": "Pos"
                            }
                        )


                        # Make player names clickable
                        role_display["Player"] = role_data.apply(
                            lambda row: (
                                f"?profile_player={row['Player']}"
                                f"&profile_team={row['Team']}"
                                f"&profile_season={row['Year']}"
                            ),
                            axis=1
                        )

                        st.dataframe(
                            role_display,
                            use_container_width=True,
                            hide_index=True,
                            height=350,
                            column_config={
                                "Player": st.column_config.LinkColumn(
                                    "Player",
                                    display_text=r"\?profile_player=(.*?)&profile_team="
                                )
                            }
                        )


    else:
        st.info(
            "No players found for this team and season."
        )

# --------------------------------------------------
# RECRUITMENT FOCUS
# --------------------------------------------------

elif page == "Recruitment Focus":

    import pandas as pd

    st.title("Recruitment Focus")

    # --------------------------------------------------
    # LOAD AND PREPARE DATA
    # --------------------------------------------------

    score_data = scores.copy()
    stats_data = players.copy()

    score_columns = [
        "FB Score",
        "CB Score",
        "BPCB Score",
        "BWM Score",
        "DLP Score",
        "B2BM Score",
        "AP Score",
        "WG Score",
        "IW Score",
        "CF Score",
    ]

    # Find xG and xA columns, allowing for different naming conventions.
    def find_stat_column(data, candidates):
        for column in candidates:
            if column in data.columns:
                return column
        return None

    xg_source = find_stat_column(
        stats_data,
        ["xG", "xG_p90", "xG per 90", "Expected_goals", "Expected_goals_p90"]
    )

    xa_source = find_stat_column(
        stats_data,
        ["xA", "xA_p90", "xA per 90", "Expected_assists", "Expected_assists_p90"]
    )

    # Build a statistics dataset with only the fields needed.
    stats_columns = [
        column for column in [
            "Player",
            "Team",
            "Current_Team",
            "League",
            "Year",
            "Passport_country",
            xg_source,
            xa_source,
        ]
        if column is not None and column in stats_data.columns
    ]

    stats_lookup = stats_data[stats_columns].copy()

    # Standardise the team field where necessary.
    if "Team" not in stats_lookup.columns and "Current_Team" in stats_lookup.columns:
        stats_lookup = stats_lookup.rename(
            columns={"Current_Team": "Team"}
        )

    # Join statistics to scoring data.
    join_columns = [
        column for column in ["Player", "Team", "League", "Year"]
        if column in score_data.columns
        and column in stats_lookup.columns
    ]

    if not join_columns:
        join_columns = [
            column for column in ["Player"]
            if column in score_data.columns
            and column in stats_lookup.columns
        ]

    if join_columns:

        stats_lookup = stats_lookup.drop_duplicates(
            subset=join_columns
        )

        extra_columns = [
            column for column in [
                "Passport_country",
                xg_source,
                xa_source,
            ]
            if column is not None
            and column in stats_lookup.columns
            and column not in score_data.columns
        ]

        if extra_columns:
            score_data = score_data.merge(
                stats_lookup[join_columns + extra_columns],
                on=join_columns,
                how="left"
            )

    # Rename xG and xA to consistent display names.
    rename_columns = {}

    if xg_source and xg_source in score_data.columns:
        rename_columns[xg_source] = "xG"

    if xa_source and xa_source in score_data.columns:
        rename_columns[xa_source] = "xA"

    score_data = score_data.rename(columns=rename_columns)

    for column in ["xG", "xA"]:
        if column not in score_data.columns:
            score_data[column] = pd.NA

    # --------------------------------------------------
    # POSITION GROUPS AND SCORING
    # --------------------------------------------------

    position_groups = {
        "Full Backs": ["RB", "LB", "RWB", "LWB"],
        "Centre Backs": ["CB"],
        "Centre Midfielders": ["CM", "DM"],
        "Attacking Midfielders": ["AM"],
        "Wingers": ["LW", "RW"],
        "Centre Forwards": ["CF"],
    }

    group_score_map = {
        "Full Backs": "FB Score",
        "Centre Backs": "CB Score",
        "Centre Midfielders": "DLP Score",
        "Attacking Midfielders": "AP Score",
        "Wingers": "WG Score",
        "Centre Forwards": "CF Score",
    }

    position_options = ["All positions"] + list(position_groups.keys())

    # Standardise position values.
    score_data["Position"] = (
        score_data["Position"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Normalise season values for consistent filtering and display.
    score_data["Year"] = score_data["Year"].astype("string")

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------

    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(
        [1.4, 1.2, 1.4, 1.5, 1.8],
        gap="medium"
    )

    with filter_col1:
        leagues = sorted(
            score_data["League"].dropna().unique().tolist()
        )

        selected_league = st.selectbox(
            "League",
            ["All leagues"] + leagues,
            key="recruitment_league"
        )

    with filter_col2:
        seasons = sorted(
            score_data["Year"].dropna().unique().tolist(),
            key=str,
            reverse=True
        )

        selected_season = st.selectbox(
            "Season",
            ["All seasons"] + seasons,
            key="recruitment_season"
        )

    with filter_col3:
        selected_position = st.selectbox(
            "Position",
            position_options,
            key="recruitment_position"
        )

    with filter_col4:
        max_minutes = st.selectbox(
            "Maximum % of minutes",
            options=[25, 50, 75, 100],
            index=3,
            format_func=lambda x: f"{x}%",
            key="recruitment_max_minutes"
        )

    with filter_col5:
        player_search = st.text_input(
            "Player name",
            placeholder="Search players...",
            key="recruitment_player_search"
        )

    # --------------------------------------------------
    # APPLY FILTERS
    # --------------------------------------------------

    recruitment_data = score_data.copy()

    if selected_league != "All leagues":
        recruitment_data = recruitment_data[
            recruitment_data["League"] == selected_league
        ]

    if selected_season != "All seasons":
        recruitment_data = recruitment_data[
            recruitment_data["Year"] == selected_season
        ]

    if selected_position != "All positions":
        positions_in_group = position_groups[selected_position]

        recruitment_data = recruitment_data[
            recruitment_data["Position"].isin(positions_in_group)
        ]

    if "Mins_pct" in recruitment_data.columns:
        recruitment_data = recruitment_data[
            pd.to_numeric(
                recruitment_data["Mins_pct"],
                errors="coerce"
            ).le(max_minutes)
        ]

    if player_search.strip():
        recruitment_data = recruitment_data[
            recruitment_data["Player"]
            .fillna("")
            .astype(str)
            .str.contains(
                player_search.strip(),
                case=False,
                na=False
            )
        ]

    # --------------------------------------------------
    # CALCULATE POSITION GROUP AND RANK
    # --------------------------------------------------

    position_to_group = {
        position: group
        for group, positions in position_groups.items()
        for position in positions
    }

    recruitment_data = recruitment_data.copy()

    recruitment_data["Position Group"] = (
        recruitment_data["Position"].map(position_to_group)
    )

    def get_player_score(row):
        group = row.get("Position Group")

        if pd.isna(group):
            return pd.NA

        score_column = group_score_map[group]

        if score_column in row.index:
            return row[score_column]

        return pd.NA

    recruitment_data["Recruitment Score"] = recruitment_data.apply(
        get_player_score,
        axis=1
    )

    recruitment_data["Recruitment Score"] = pd.to_numeric(
        recruitment_data["Recruitment Score"],
        errors="coerce"
    )

    # Exclude players without a relevant positional score.
    recruitment_data = recruitment_data[
        recruitment_data["Recruitment Score"].notna()
    ].copy()

    # Rank players within their position group.
    if not recruitment_data.empty:
        recruitment_data["Rank"] = (
            recruitment_data
            .groupby("Position Group")["Recruitment Score"]
            .rank(method="min", ascending=False)
            .astype(int)
        )

        recruitment_data = recruitment_data.sort_values(
            ["Position Group", "Recruitment Score"],
            ascending=[True, False]
        )

    # --------------------------------------------------
    # DISPLAY TABLE
    # --------------------------------------------------

    st.subheader("Player Rankings")

    st.caption(
        f"{len(recruitment_data)} players match your filters. "
        "Players are ranked within their position group using the relevant score."
    )

    if recruitment_data.empty:

        st.info(
            "No players match these filters. "
            "Try changing the league, season, position or minutes limit."
        )

    else:

        # Player information columns.
        display_columns = [
            "Year",
            "Player",
            "Position",
            "Age",
            "Passport_country",
            "Matches_played",
            "Goals",
            "Assists",
            "xG",
            "xA",
        ]

        # If a group is selected, show only its relevant score.
        if selected_position != "All positions":

            relevant_score = group_score_map[selected_position]

            available_score_columns = [
                relevant_score
            ] if (
                relevant_score in recruitment_data.columns
                and recruitment_data[relevant_score].notna().any()
            ) else []

        else:
            # When all positions are selected, show every score
            # that has at least one non-NA value in the results.
            available_score_columns = [
                column for column in score_columns
                if column in recruitment_data.columns
                and recruitment_data[column].notna().any()
            ]

        display_columns = [
            column for column in display_columns
            if column in recruitment_data.columns
        ]

        # Put score columns after player information.
        display_columns += available_score_columns

        # Place Rank immediately before the score column(s).
        if available_score_columns:
            first_score_index = display_columns.index(
                available_score_columns[0]
            )
            display_columns.insert(first_score_index, "Rank")
        else:
            display_columns.insert(0, "Rank")

        display_data = recruitment_data[display_columns].copy()

        display_data = display_data.rename(
            columns={
                "Year": "Season",
                "Player": "Name",
                "Position": "Pos",
                "Passport_country": "Nationality",
                "Matches_played": "Apps",
            }
        )

        # Round expected-goal and score values.
        for column in ["xG", "xA"] + available_score_columns:
            if column in display_data.columns:
                display_data[column] = pd.to_numeric(
                    display_data[column],
                    errors="coerce"
                ).round(2)


        # Make player names clickable
        display_data["Name"] = recruitment_data.apply(
            lambda row: (
                f"?profile_player={row['Player']}"
                f"&profile_team={row['Team']}"
                f"&profile_season={row['Year']}"
            ),
            axis=1
        )

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True,
            height=650,
            column_config={
                "Name": st.column_config.LinkColumn(
                    "Name",
                    display_text=r"\?profile_player=(.*?)&profile_team="
                ),
                "Rank": st.column_config.NumberColumn(
                    "Rank",
                    format="%d"
                ),
                "Age": st.column_config.NumberColumn(
                    "Age",
                    format="%d"
                ),
                "Apps": st.column_config.NumberColumn(
                    "Apps",
                    format="%d"
                ),
                "Goals": st.column_config.NumberColumn(
                    "Goals",
                    format="%d"
                ),
                "Assists": st.column_config.NumberColumn(
                    "Assists",
                    format="%d"
                ),
            }
        )


# --------------------------------------------------
# PLAYER PROFILES
# --------------------------------------------------

elif page == "Player Profiles":

    import pandas as pd
    import plotly.graph_objects as go

    st.title("Player Profiles")

    # --------------------------------------------------
    # LOAD PLAYER DATA
    # --------------------------------------------------

    profile_data = players.copy()
    profile_data["Year"] = profile_data["Year"].astype("string")


    # --------------------------------------------------
    # PLAYER SELECTORS
    # --------------------------------------------------

    # Retrieve the player requested by the clicked link
    requested_player = st.session_state.pop(
        "profile_player_to_open", None
    )
    requested_team = st.session_state.pop(
        "profile_team_to_open", None
    )
    requested_season = st.session_state.pop(
        "profile_season_to_open", None
    )

    col1, col2, col3 = st.columns(
        [1.5, 1, 1.5], gap="medium"
    )

    # TEAM
    with col1:
        teams = sorted(
            profile_data["Team"].dropna().unique().tolist()
        )

        if requested_team in teams:
            st.session_state["profile_team"] = requested_team
        elif "profile_team" not in st.session_state and teams:
            st.session_state["profile_team"] = teams[0]

        selected_team = st.selectbox(
            "Team",
            teams,
            key="profile_team"
        )

    team_players = profile_data[
        profile_data["Team"] == selected_team
    ].copy()

    # SEASON
    with col2:
        seasons = sorted(
            team_players["Year"].dropna().unique().tolist(),
            key=str,
            reverse=True
        )

        if requested_season is not None:
            requested_season = str(requested_season)

        if requested_season in seasons:
            st.session_state["profile_season"] = requested_season
        elif (
            "profile_season" not in st.session_state
            or st.session_state["profile_season"] not in seasons
        ) and seasons:
            st.session_state["profile_season"] = seasons[0]

        selected_season = st.selectbox(
            "Season",
            seasons,
            key="profile_season"
        )

    season_players = team_players[
        team_players["Year"] == selected_season
    ].copy()

    # PLAYER
    with col3:
        player_names = sorted(
            season_players["Player"].dropna().unique().tolist()
        )

        if requested_player in player_names:
            st.session_state["profile_player"] = requested_player
        elif (
            "profile_player" not in st.session_state
            or st.session_state["profile_player"] not in player_names
        ) and player_names:
            st.session_state["profile_player"] = player_names[0]

        selected_player = st.selectbox(
            "Player",
            player_names,
            key="profile_player"
        )

    # --------------------------------------------------
    # SELECT PLAYER RECORD
    # --------------------------------------------------

    player_record = season_players[
        season_players["Player"] == selected_player
    ].iloc[0]

    # --------------------------------------------------
    # AUTOMATIC POSITION GROUPING
    # --------------------------------------------------

    player_position = str(
        player_record.get("Position", "")
    ).strip().upper()

    if player_position in ["RB", "LB", "RWB", "LWB"]:
        role = "FB"
    elif player_position == "CB":
        role = "CB"
    elif player_position == "DM":
        role = "DM"
    elif player_position == "CM":
        role = "CM"
    elif player_position == "AM":
        role = "AM"
    elif player_position in ["LW", "RW"]:
        role = "WG"
    elif player_position == "CF":
        role = "CF"
    else:
        role = None

    if role is not None:
        chart_metrics = list(dict.fromkeys(ROLE_METRICS[role]))
        comparison_positions = POSITION_GROUPS[role]["positions"]
        chart_title = POSITION_GROUPS[role]["title"]
    else:
        chart_metrics = []
        comparison_positions = []
        chart_title = "Position Profile"

    # --------------------------------------------------
    # PLAYER HEADER
    # --------------------------------------------------

    position_score_map = {
        "RB": "FB Score",
        "LB": "FB Score",
        "RWB": "FB Score",
        "LWB": "FB Score",
        "CB": "CB Score",
        "CM": "DLP Score",
        "DM": "DLP Score",
        "AM": "AP Score",
        "LW": "WG Score",
        "RW": "WG Score",
        "CF": "CF Score",
    }

    player_position = str(
        player_record.get("Position", "")
    ).strip().upper()

    score_column = position_score_map.get(player_position)
    player_score = None

    if score_column and score_column in scores.columns:
        score_match = scores[
            (scores["Player"].astype(str) == str(selected_player))
            & (scores["Year"].astype(str) == str(selected_season))
        ].copy()

        if "Current_Team" in score_match.columns:
            team_match = (
                score_match["Current_Team"].astype(str) == str(selected_team)
            )
            if team_match.any():
                score_match = score_match[team_match]
        elif "Team" in score_match.columns:
            team_match = (
                score_match["Team"].astype(str) == str(selected_team)
            )
            if team_match.any():
                score_match = score_match[team_match]

        if not score_match.empty:
            player_score = pd.to_numeric(
                score_match.iloc[0][score_column],
                errors="coerce"
            )

    def get_score_colour(value):
        if value is None or pd.isna(value):
            return "#929292"
        elif value <= 34:
            return "#FF0000"
        elif value <= 49:
            return "#FF9A00"
        elif value <= 69:
            return "#FFFF33"
        elif value <= 79:
            return "#C6FF4A"
        return "#00A340"

    score_text = (
    f"{int(player_score)}"
    if player_score is not None and pd.notna(player_score)
    else "N/A"
)
    score_colour = get_score_colour(player_score)

    header_col, score_col = st.columns([8, 1])

    with header_col:
        st.markdown(
            f"""
            <div style="
                padding: 8px 0 16px 0;
                border-bottom: 2px solid #C8A64B;
                margin-bottom: 18px;
            ">
                <div style="
                    font-size: 28px;
                    font-weight: 700;
                    color: #171717;
                ">{selected_player}</div>
                <div style="
                    font-size: 15px;
                    color: #666666;
                    margin-top: 4px;
                ">
                    {player_record.get("Position", "N/A")}
                    &nbsp; | &nbsp;
                    {selected_team}
                    &nbsp; | &nbsp;
                    {int(player_record["Age"]) if pd.notna(player_record.get("Age")) else "N/A"}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with score_col:
        st.markdown(
            f"""
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                width: 72px;
                height: 62px;
                margin: 8px 0 18px auto;
                border-radius: 9px;
                background-color: {score_colour};
                color: #171717;
                box-sizing: border-box;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
            ">
                <span style="
                    font-size: 9px;
                    font-weight: 700;
                    letter-spacing: 1.2px;
                    text-transform: uppercase;
                ">Score</span>
                <span style="
                    font-size: 25px;
                    font-weight: 750;
                    line-height: 1.15;
                ">{score_text}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    # --------------------------------------------------
    # MAIN PROFILE LAYOUT
    # --------------------------------------------------

    left_col, right_col = st.columns([1.15, 1], gap="large")

           # --------------------------------------------------
    # LEFT: PERCENTILE CHART
    # --------------------------------------------------

    with left_col:

        st.subheader(chart_title)

        if role is None:
            st.warning(
                f"No percentile profile is configured for position "
                f"'{player_position}'."
            )

        else:
            st.caption(
        f"Comparing against: {', '.join(comparison_positions)}"
        f" | {selected_season} Data"
        " | Minimum 400 minutes"
    )

            # ------------------------------------------
            # PREPARE DATA
            # Keep the existing percentile calculation
            # ------------------------------------------

            percentile_data = players.copy()

            percentile_data["Year"] = (
                percentile_data["Year"].astype(str)
            )

            percentile_data["Position"] = (
                percentile_data["Position"].astype(str).str.upper()
            )

            percentile_data["Minutes_played"] = pd.to_numeric(
                percentile_data["Minutes_played"],
                errors="coerce"
            )

            target_mask = (
                (percentile_data["Player"] == selected_player)
                & (percentile_data["Team"] == selected_team)
                & (percentile_data["Year"] == str(selected_season))
            )

            target_rows = percentile_data[target_mask]

            if target_rows.empty:
                st.warning("No matching player record was found.")

            else:
                target_row = target_rows.iloc[0]

                # Comparison group and minimum-minutes filter
                peer_mask = (
                    percentile_data["Position"].isin(
                        comparison_positions
                    )
                    | target_mask
                ) & (
                    percentile_data["Minutes_played"] >= 200
                )

                peers = percentile_data.loc[peer_mask].copy()

                # --------------------------------------
                # METRIC LABELS
                # --------------------------------------

                metric_labels = {
                    "Goals": "Goals",
                    "Goals_p90": "Goals p90",
                    "xG_p90": "xG p90",
                    "Assists": "Assists",
                    "xA_p90": "xA p90",
                    "Successful_attacking_actions_p90":
                        "Attacking Actions p90",
                    "Passes_p90": "Passes p90",
                    "Accurate_passes_pct": "Pass Accuracy %",
                    "Accurate_progressive_passes_pct":
                        "Progressive Pass Accuracy %",
                    "Progressive_passes_p90":
                        "Progressive Passes p90",
                    "Forward_passes_p90": "Forward Passes p90",
                    "Lateral_passes_p90": "Lateral Passes p90",
                    "Defensive_duels_won_pct":
                        "Defensive Duel Win %",
                    "Successful_defensive_actions_p90":
                        "Defensive Actions p90",
                    "Offensive_duels_p90": "Offensive Duels p90",
                    "PAdj_Interceptions": "PAdj Interceptions",
                    "Aerial_duels_won_pct": "Aerial Duel Win %",
                    "Key_passes_p90": "Key Passes p90",
                    "Progressive_runs_p90": "Progressive Runs p90",
                    "Successful_dribbles_pct": "Dribble Success %",
                    "Dribbles_p90": "Dribbles p90",
                    "Deep_completions_p90": "Deep Completions p90",
                    "Accurate_crosses_pct": "Cross Accuracy %",
                    "Crosses_p90": "Crosses p90",
                    "Touches_in_box_p90": "Touches in Box p90",
                    "Goal_conversion_pct": "Goal Conversion %",
                    "Shots_on_target_pct": "Shots on Target %",
                    "Aerial_duels_p90": "Aerial Duels p90",
                    "Defensive_duels_p90": "Defensive Duels p90",
                    "PAdj_Sliding_tackles": "PAdj Sliding Tackles",
                }

                # --------------------------------------
                # CALCULATE PERCENTILES
                # --------------------------------------

                chart_data = []

                for metric in chart_metrics:

                    if metric not in percentile_data.columns:
                        continue

                    if metric not in peers.columns:
                        continue

                    target_value = pd.to_numeric(
                        pd.Series([target_row[metric]]),
                        errors="coerce"
                    ).iloc[0]

                    if pd.isna(target_value):
                        continue

                    peer_values = pd.to_numeric(
                        peers[metric],
                        errors="coerce"
                    ).dropna()

                    if peer_values.empty:
                        continue

                    # Preserve the existing percentile method
                    percentile = round(
                        (peer_values <= target_value).sum()
                        / len(peer_values)
                        * 100,
                        0
                    )

                    chart_data.append({
                        "Metric": metric,
                        "Label": metric_labels.get(
                            metric,
                            metric.replace("_", " ")
                        ),
                        "Percentile": percentile,
                    })

                # --------------------------------------
                # DRAW CIRCULAR CHART
                # --------------------------------------

                if not chart_data:
                    st.warning(
                        "No usable percentile metrics were found."
                    )

                else:
                    chart_df = pd.DataFrame(chart_data)

                    # ----------------------------------
                    # PERCENTILE BAR COLOURS
                    # ----------------------------------

                    def get_band_colour(value):
                        if value <= 34:
                            return "#FF0000"
                        elif value <= 49:
                            return "#FF9A00"
                        elif value <= 69:
                            return "#FFFF33"
                        elif value <= 79:
                            return "#C6FF4A"
                        return "#00A340"

                    chart_df["Colour"] = (
                        chart_df["Percentile"].apply(get_band_colour)
                    )

                    # ----------------------------------
                    # LIGHTER BACKGROUND COLOURS
                    # Each segment matches its own bar
                    # ----------------------------------

                    def get_tier(value):
                        if value <= 34:
                            return "Tier1"
                        elif value <= 49:
                            return "Tier2"
                        elif value <= 69:
                            return "Tier3"
                        return "Tier4"

                    tier_colours = {
                        "Tier1": "#FFF0F0",
                        "Tier2": "#FFF3E8",
                        "Tier3": "#FFFFE8",
                        "Tier4": "#F0FFF8",
                    }

                    chart_df["Tier"] = (
                        chart_df["Percentile"].apply(get_tier)
                    )

                    chart_df["BackgroundColour"] = (
                        chart_df["Tier"].map(tier_colours)
                    )

                    # ----------------------------------
                    # CHART ANGLES AND LABELS
                    # ----------------------------------

                    metric_count = len(chart_df)

                    chart_df["Angle"] = [
                        i * 360 / metric_count
                        for i in range(metric_count)
                    ]

                    chart_df["DisplayLabel"] = (
                        chart_df["Label"]
                        .str.replace("Successful ", "", regex=False)
                    )

                    # ----------------------------------
                    # FIGURE
                    # ----------------------------------

                    fig = go.Figure()

                    # Outer background ring
                    # Each segment uses its own lighter colour
                    fig.add_trace(
                        go.Barpolar(
                            r=[8] * metric_count,
                            theta=chart_df["Angle"],
                            base=[102] * metric_count,
                            width=[
                                360 / metric_count * 0.96
                            ] * metric_count,
                            marker=dict(
                                color=chart_df["BackgroundColour"],
                                line=dict(
                                    color="#B8B8B8",
                                    width=0.7,
                                ),
                            ),
                            hoverinfo="skip",
                            showlegend=False,
                            name="Profile background",
                        )
                    )

                    # Percentile bars
                    fig.add_trace(
                        go.Barpolar(
                            r=chart_df["Percentile"],
                            theta=chart_df["Angle"],
                            base=[0] * metric_count,
                            width=[
                                360 / metric_count * 0.90
                            ] * metric_count,
                            marker=dict(
                                color=chart_df["Colour"],
                                line=dict(
                                    color="#333333",
                                    width=0.8,
                                ),
                            ),
                            customdata=chart_df[
                                ["Label", "Percentile"]
                            ],
                            hovertemplate=(
                                "<b>%{customdata[0]}</b>"
                                "<br>Percentile: %{customdata[1]:.0f}"
                                "<extra></extra>"
                            ),
                            showlegend=False,
                            name="Percentile",
                        )
                    )

                    # ----------------------------------
                    # PERCENTILE LABELS INSIDE THE BARS
                    # ----------------------------------

                    label_radii = [
                        max(value - 7, 7)
                        for value in chart_df["Percentile"]
                    ]

                    fig.add_trace(
                        go.Scatterpolar(
                            r=label_radii,
                            theta=chart_df["Angle"],
                            mode="markers+text",
                            text=[
                                f"{value:.0f}"
                                for value in chart_df["Percentile"]
                            ],
                            textposition="middle center",
                            textfont=dict(
                                size=10,
                                color="#171717",
                                family="Arial",
                            ),
                            marker=dict(
                                size=21,
                                color="white",
                                line=dict(
                                    color="#333333",
                                    width=0.8,
                                ),
                                symbol="square",
                            ),
                            hoverinfo="skip",
                            showlegend=False,
                            name="Percentile labels",
                        )
                    )

                    # ----------------------------------
                    # LAYOUT AND SPACING
                    # ----------------------------------

                    fig.update_layout(
                        height=780,
                        autosize=True,
                        margin=dict(
                            l=95,
                            r=95,
                            t=35,
                            b=95,
                        ),
                        paper_bgcolor="white",
                        plot_bgcolor="white",
                        font=dict(
                            family="Arial",
                            color="#171717",
                        ),
                        showlegend=False,
                        barmode="overlay",
                        polar=dict(
                            bgcolor="white",
                            radialaxis=dict(
                                range=[0, 122],
                                showticklabels=False,
                                ticks="",
                                showline=False,
                                showgrid=True,
                                gridcolor="#E2E2E2",
                                gridwidth=0.7,
                            ),
                            angularaxis=dict(
                                rotation=90,
                                direction="clockwise",
                                tickmode="array",
                                tickvals=chart_df["Angle"],
                                ticktext=chart_df["DisplayLabel"],
                                tickfont=dict(
                                    size=10,
                                    color="#333333",
                                ),
                                ticks="",
                                showline=False,
                                showgrid=False,
                            ),
                        ),
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        config={
                            "displayModeBar": False,
                            "responsive": True,
                        },
                    )

    # --------------------------------------------------
    # RIGHT: SCATTER PLOTS
    # --------------------------------------------------

    with right_col:
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")


        if role not in SCATTER_METRICS:
            st.warning(
                f"No scatter plot configuration exists for "
                f"position '{player_position}'."
            )

        else:
            position_scatter = SCATTER_METRICS[role]

            # ------------------------------------------
            # PREPARE DATA
            # ------------------------------------------

            scatter_data = players.copy()

            scatter_data["Year"] = (
                scatter_data["Year"].astype(str)
            )

            scatter_data["Position"] = (
                scatter_data["Position"].astype(str).str.upper()
            )

            scatter_data["Minutes_played"] = pd.to_numeric(
                scatter_data["Minutes_played"],
                errors="coerce",
            )

            scatter_data["League"] = (
                scatter_data["League"].fillna("Unknown").astype(str)
            )

            target_mask = (
                (scatter_data["Player"] == selected_player)
                & (scatter_data["Team"] == selected_team)
                & (scatter_data["Year"] == str(selected_season))
            )

            peer_mask = (
                scatter_data["Position"].isin(comparison_positions)
                | target_mask
            ) & (
                scatter_data["Year"] == str(selected_season)
            ) & (
                scatter_data["Minutes_played"] >= 200
            )

            scatter_data = scatter_data.loc[peer_mask].copy()

            scatter_data["Selected"] = (
                (scatter_data["Player"] == selected_player)
                & (scatter_data["Team"] == selected_team)
                & (scatter_data["Year"] == str(selected_season))
            )

            # ------------------------------------------
            # LEAGUE COLOURS
            # ------------------------------------------

            league_palette = [
                "#2878B5",  # Blue
                "#E08B36",  # Orange
                "#35A776",  # Green
                "#D65F59",  # Red
                "#8B6BB1",  # Purple
            ]

            # Keep known league colours consistent
            league_colour_map = {
                "Scottish L1": "#2878B5",
                "Scottish L2": "#E08B36",
            }

            available_leagues = sorted(
                scatter_data["League"].unique()
            )

            next_colour = 0

            for league in available_leagues:
                if league not in league_colour_map:
                    used_colours = set(league_colour_map.values())

                    while (
                        league_palette[next_colour % len(league_palette)]
                        in used_colours
                    ):
                        next_colour += 1

                    league_colour_map[league] = (
                        league_palette[next_colour % len(league_palette)]
                    )

                    next_colour += 1

            scatter_data["LeagueColour"] = (
                scatter_data["League"].map(league_colour_map)
            )

            # ------------------------------------------
            # SCATTER PLOT FUNCTION
            # ------------------------------------------

            def create_scatter_plot(data, metric_config, plot_title):

                x_metric = metric_config["x"]
                y_metric = metric_config["y"]

                x_label = metric_config["x_label"]
                y_label = metric_config["y_label"]

                missing = [
                    metric
                    for metric in [x_metric, y_metric]
                    if metric not in data.columns
                ]

                if missing:
                    st.warning(
                        f"{plot_title} cannot be displayed because "
                        f"these metrics are missing: "
                        f"{', '.join(missing)}."
                    )
                    return

                plot_data = data.copy()

                plot_data[x_metric] = pd.to_numeric(
                    plot_data[x_metric],
                    errors="coerce",
                )

                plot_data[y_metric] = pd.to_numeric(
                    plot_data[y_metric],
                    errors="coerce",
                )

                plot_data = plot_data.dropna(
                    subset=[x_metric, y_metric]
                )

                if plot_data.empty:
                    st.info(
                        f"No players have usable data for {plot_title}."
                    )
                    return

                comparison = plot_data[
                    ~plot_data["Selected"]
                ]

                selected = plot_data[
                    plot_data["Selected"]
                ]

                fig = go.Figure()

                # --------------------------------------
                # COMPARISON PLAYERS BY LEAGUE
                # --------------------------------------

                for league in available_leagues:

                    league_players = comparison[
                        comparison["League"] == league
                    ]

                    if league_players.empty:
                        continue

                    fig.add_trace(
                        go.Scatter(
                            x=league_players[x_metric],
                            y=league_players[y_metric],
                            mode="markers",
                            name=league,
                            text=league_players["Player"],
                            customdata=league_players[
                                ["Team", "Minutes_played"]
                            ].to_numpy(),
                            marker=dict(
                                size=8,
                                color=league_colour_map[league],
                                opacity=0.82,
                                line=dict(
                                    color="white",
                                    width=0.5,
                                ),
                            ),
                            hovertemplate=(
                                "<b>%{text}</b>"
                                "<br>Team: %{customdata[0]}"
                                f"<br>{x_label}: "
                                "%{x:.2f}"
                                f"<br>{y_label}: "
                                "%{y:.2f}"
                                "<br>Minutes: %{customdata[1]:.0f}"
                                "<extra></extra>"
                            ),
                        )
                    )

                # --------------------------------------
                # AVERAGE REFERENCE LINES AND QUADRANTS
                # --------------------------------------

                if not comparison.empty:

                    x_mean = comparison[x_metric].mean()
                    y_mean = comparison[y_metric].mean()

                    fig.add_vline(
                        x=x_mean,
                        line_dash="dash",
                        line_color="#B0B0B0",
                        line_width=1,
                    )

                    fig.add_hline(
                        y=y_mean,
                        line_dash="dash",
                        line_color="#B0B0B0",
                        line_width=1,
                    )

                    x_min = plot_data[x_metric].min()
                    x_max = plot_data[x_metric].max()
                    y_min = plot_data[y_metric].min()
                    y_max = plot_data[y_metric].max()

                    x_range = max(x_max - x_min, 0.01)
                    y_range = max(y_max - y_min, 0.01)

                    quadrant_annotations = [
                        (
                            x_min + x_range * 0.03,
                            y_max - y_range * 0.04,
                            "",
                            "left",
                            "top",
                        ),
                        (
                            x_max - x_range * 0.03,
                            y_max - y_range * 0.04,
                            "",
                            "right",
                            "top",
                        ),
                        (
                            x_min + x_range * 0.03,
                            y_min + y_range * 0.04,
                            "",
                            "left",
                            "bottom",
                        ),
                        (
                            x_max - x_range * 0.03,
                            y_min + y_range * 0.04,
                            "",
                            "right",
                            "bottom",
                        ),
                    ]

                    for (
                        x_pos,
                        y_pos,
                        label,
                        x_anchor,
                        y_anchor,
                    ) in quadrant_annotations:

                        fig.add_annotation(
                            x=x_pos,
                            y=y_pos,
                            text=label,
                            showarrow=False,
                            xanchor=x_anchor,
                            yanchor=y_anchor,
                            font=dict(
                                size=9,
                                color="#A0A0A0",
                            ),
                        )

                # --------------------------------------
                # SELECTED PLAYER
                # --------------------------------------

                if not selected.empty:

                    fig.add_trace(
                        go.Scatter(
                            x=selected[x_metric],
                            y=selected[y_metric],
                            mode="markers+text",
                            name=selected_player,
                            text=selected["Player"],
                            textposition="top center",
                            textfont=dict(
                                size=11,
                                color="#171717",
                            ),
                            marker=dict(
                                size=14,
                                color="#C8A64B",
                                symbol="circle",
                                line=dict(
                                    color="#8A7133",
                                    width=1,
                                ),
                            ),
                            customdata=selected[
                                ["Team", "Minutes_played"]
                            ].to_numpy(),
                            hovertemplate=(
                                "<b>%{text}</b>"
                                "<br>Team: %{customdata[0]}"
                                f"<br>{x_label}: "
                                "%{x:.2f}"
                                f"<br>{y_label}: "
                                "%{y:.2f}"
                                "<br>Minutes: %{customdata[1]:.0f}"
                                "<extra></extra>"
                            ),
                        )
                    )

                # --------------------------------------
                # CHART LAYOUT
                # --------------------------------------

                fig.update_layout(
                    title=dict(
                        text=plot_title,
                        x=0,
                        xanchor="left",
                        font=dict(
                            size=16,
                            color="#171717",
                        ),
                    ),
                    height=360,
                    autosize=True,
                    margin=dict(
                        l=55,
                        r=130,
                        t=55,
                        b=55,
                    ),
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font=dict(
                        family="Arial",
                        size=11,
                        color="#171717",
                    ),
                    showlegend=True,
                    legend=dict(
                        title=dict(text="League"),
                        orientation="v",
                        x=1.02,
                        xanchor="left",
                        y=0.5,
                        yanchor="middle",
                        font=dict(size=10),
                    ),
                    xaxis=dict(
                        title=x_label,
                        showgrid=True,
                        gridcolor="#EAEAEA",
                        zeroline=False,
                        showline=False,
                    ),
                    yaxis=dict(
                        title=y_label,
                        showgrid=True,
                        gridcolor="#EAEAEA",
                        zeroline=False,
                        showline=False,
                    ),
                )

                # --------------------------------------
                # DISPLAY CHART
                # --------------------------------------

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={
                        "displayModeBar": False,
                        "responsive": True,
                    },
                )

                excluded_count = len(data) - len(plot_data)

                if excluded_count > 0:
                    st.caption(
                        f"{excluded_count} records excluded from this "
                        "plot because one or both plotted metrics "
                        "were missing."
                    )

            # ------------------------------------------
            # ATTACKING SCATTER PLOT
            # ------------------------------------------

            create_scatter_plot(
                scatter_data,
                position_scatter["attacking"],
                position_scatter["attacking"]["title"],
            )

            # ------------------------------------------
            # DEFENDING SCATTER PLOT
            # ------------------------------------------

            create_scatter_plot(
                scatter_data,
                position_scatter["defending"],
                position_scatter["defending"]["title"],
            )

# --------------------------------------------------
# PLAYER COMPARISON
# --------------------------------------------------

elif page == "Player Comparison":

    import plotly.graph_objects as go

    st.title("Player Comparison")


    # --------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------

    comparison_data = players.copy()

    comparison_data["Year"] = (
        comparison_data["Year"].astype(str)
    )

    comparison_data["Position"] = (
        comparison_data["Position"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    comparison_data["Minutes_played"] = pd.to_numeric(
        comparison_data["Minutes_played"],
        errors="coerce"
    )

    player_options = sorted(
        comparison_data["Player"].dropna().unique().tolist()
    )

    if not player_options:
        st.warning("No players are available.")
        st.stop()

    # --------------------------------------------------
    # METRIC LABELS
    # --------------------------------------------------

    metric_labels = {
        "Goals": "Goals",
        "Goals_p90": "Goals p90",
        "xG_p90": "xG p90",
        "Assists": "Assists",
        "xA_p90": "xA p90",
        "Successful_attacking_actions_p90": "Attacking Actions p90",
        "Passes_p90": "Passes p90",
        "Accurate_passes_pct": "Pass Accuracy %",
        "Accurate_progressive_passes_pct": "Progressive Pass Accuracy %",
        "Progressive_passes_p90": "Progressive Passes p90",
        "Forward_passes_p90": "Forward Passes p90",
        "Lateral_passes_p90": "Lateral Passes p90",
        "Defensive_duels_won_pct": "Defensive Duel Win %",
        "Successful_defensive_actions_p90": "Defensive Actions p90",
        "Offensive_duels_p90": "Offensive Duels p90",
        "PAdj_Interceptions": "PAdj Interceptions",
        "Aerial_duels_won_pct": "Aerial Duel Win %",
        "Key_passes_p90": "Key Passes p90",
        "Progressive_runs_p90": "Progressive Runs p90",
        "Successful_dribbles_pct": "Dribble Success %",
        "Dribbles_p90": "Dribbles p90",
        "Deep_completions_p90": "Deep Completions p90",
        "Accurate_crosses_pct": "Cross Accuracy %",
        "Crosses_p90": "Crosses p90",
        "Touches_in_box_p90": "Touches in Box p90",
        "Goal_conversion_pct": "Goal Conversion %",
        "Shots_on_target_pct": "Shots on Target %",
        "Aerial_duels_p90": "Aerial Duels p90",
        "Defensive_duels_p90": "Defensive Duels p90",
        "PAdj_Sliding_tackles": "PAdj Sliding Tackles",
    }

    # --------------------------------------------------
    # CIRCULAR CHART FUNCTION
    # --------------------------------------------------

    def comparison_circle_chart(player_name, season, chart_key):

        target_mask = (
            (comparison_data["Player"] == player_name)
            & (comparison_data["Year"] == str(season))
        )

        target_rows = comparison_data[target_mask]

        if target_rows.empty:
            st.warning("No matching player record was found.")
            return

        target_row = target_rows.iloc[0]

        position = target_row["Position"]

        # Match the role logic used in Player Profiles
        if position in ["RB", "LB", "RWB", "LWB"]:
            role = "FB"
        elif position == "CB":
            role = "CB"
        elif position == "DM":
            role = "DM"
        elif position == "CM":
            role = "CM"
        elif position == "AM":
            role = "AM"
        elif position in ["LW", "RW"]:
            role = "WG"
        elif position == "CF":
            role = "CF"
        else:
            st.warning(
                f"No circular profile is configured for {position}."
            )
            return

        chart_metrics = list(dict.fromkeys(ROLE_METRICS[role]))
        comparison_positions = POSITION_GROUPS[role]["positions"]

        st.markdown(
            f"**{player_name}** — {position} | {season}"
        )

        st.caption(
            f"Compared against: {', '.join(comparison_positions)}"
            " | Minimum 200 minutes"
        )

        # Comparison group, including the selected player
        peer_mask = (
            comparison_data["Position"].isin(comparison_positions)
            | target_mask
        ) & (
            comparison_data["Minutes_played"] >= 200
        )

        peers = comparison_data.loc[peer_mask].copy()

        # Calculate percentiles using the existing method
        chart_data = []

        for metric in chart_metrics:

            if metric not in comparison_data.columns:
                continue

            target_value = pd.to_numeric(
                pd.Series([target_row[metric]]),
                errors="coerce"
            ).iloc[0]

            if pd.isna(target_value):
                continue

            peer_values = pd.to_numeric(
                peers[metric],
                errors="coerce"
            ).dropna()

            if peer_values.empty:
                continue

            percentile = round(
                (peer_values <= target_value).sum()
                / len(peer_values)
                * 100,
                0
            )

            chart_data.append({
                "Metric": metric,
                "Label": metric_labels.get(
                    metric,
                    metric.replace("_", " ")
                ),
                "Percentile": percentile,
            })

        if not chart_data:
            st.warning("No usable percentile metrics were found.")
            return

        chart_df = pd.DataFrame(chart_data)

        # Same percentile colours as Player Profiles
        def get_band_colour(value):
            if value <= 34:
                return "#FF0000"
            elif value <= 49:
                return "#FF9A00"
            elif value <= 69:
                return "#FFFF33"
            elif value <= 79:
                return "#C6FF4A"
            return "#00A340"

        def get_tier(value):
            if value <= 34:
                return "Tier1"
            elif value <= 49:
                return "Tier2"
            elif value <= 69:
                return "Tier3"
            return "Tier4"

        tier_colours = {
            "Tier1": "#FFF0F0",
            "Tier2": "#FFF3E8",
            "Tier3": "#FFFFE8",
            "Tier4": "#F0FFF8",
        }

        chart_df["Colour"] = (
            chart_df["Percentile"].apply(get_band_colour)
        )

        chart_df["BackgroundColour"] = (
            chart_df["Percentile"]
            .apply(get_tier)
            .map(tier_colours)
        )

        metric_count = len(chart_df)

        chart_df["Angle"] = [
            i * 360 / metric_count
            for i in range(metric_count)
        ]

        chart_df["DisplayLabel"] = (
            chart_df["Label"]
            .str.replace("Successful ", "", regex=False)
        )

        # Draw the circular chart
        fig = go.Figure()

        fig.add_trace(
            go.Barpolar(
                r=[8] * metric_count,
                theta=chart_df["Angle"],
                base=[102] * metric_count,
                width=[360 / metric_count * 0.96] * metric_count,
                marker=dict(
                    color=chart_df["BackgroundColour"],
                    line=dict(color="#B8B8B8", width=0.7),
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Barpolar(
                r=chart_df["Percentile"],
                theta=chart_df["Angle"],
                base=[0] * metric_count,
                width=[360 / metric_count * 0.90] * metric_count,
                marker=dict(
                    color=chart_df["Colour"],
                    line=dict(color="#333333", width=0.8),
                ),
                customdata=chart_df[["Label", "Percentile"]],
                hovertemplate=(
                    "<b>%{customdata[0]}</b>"
                    "<br>Percentile: %{customdata[1]:.0f}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatterpolar(
                r=[
                    max(value - 7, 7)
                    for value in chart_df["Percentile"]
                ],
                theta=chart_df["Angle"],
                mode="markers+text",
                text=[
                    f"{value:.0f}"
                    for value in chart_df["Percentile"]
                ],
                textposition="middle center",
                textfont=dict(
                    size=10,
                    color="#171717",
                    family="Arial",
                ),
                marker=dict(
                    size=21,
                    color="white",
                    line=dict(color="#333333", width=0.8),
                    symbol="square",
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        fig.update_layout(
            height=580,
            autosize=True,
            margin=dict(l=65, r=65, t=45, b=65),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(
                family="Arial",
                color="#171717",
            ),
            showlegend=False,
            barmode="overlay",
            polar=dict(
                bgcolor="white",
                radialaxis=dict(
                    range=[0, 122],
                    showticklabels=False,
                    ticks="",
                    showline=False,
                    showgrid=True,
                    gridcolor="#E2E2E2",
                    gridwidth=0.7,
                ),
                angularaxis=dict(
                    rotation=90,
                    direction="clockwise",
                    tickmode="array",
                    tickvals=chart_df["Angle"],
                    ticktext=chart_df["DisplayLabel"],
                    tickfont=dict(
                        size=9,
                        color="#333333",
                    ),
                    ticks="",
                    showline=False,
                    showgrid=False,
                ),
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
            key=chart_key,
        )

    # --------------------------------------------------
    # TWO SIDE-BY-SIDE PLAYER PANELS
    # --------------------------------------------------

    left_col, right_col = st.columns(2, gap="large")

    for side, column in [
        ("left", left_col),
        ("right", right_col),
    ]:

        with column:

            st.markdown(
                f"""
                <div style="
                    border-bottom: 3px solid #C8A64B;
                    padding-bottom: 8px;
                    margin-bottom: 12px;
                ">
                    <strong>{'Player 1' if side == 'left' else 'Player 2'}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

            selected_comparison_player = st.selectbox(
                "Player",
                player_options,
                key=f"comparison_{side}_player",
            )

            available_seasons = sorted(
                comparison_data.loc[
                    comparison_data["Player"] == selected_comparison_player,
                    "Year"
                ].dropna().unique().tolist(),
                key=str,
                reverse=True,
            )

            if not available_seasons:
                st.warning("No seasons are available for this player.")
                continue

            selected_comparison_season = st.selectbox(
                "Season",
                available_seasons,
                key=f"comparison_{side}_season",
            )

            st.divider()

            comparison_circle_chart(
                selected_comparison_player,
                selected_comparison_season,
                f"comparison_{side}_chart",
            )