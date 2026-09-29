import streamlit as st
import datetime
import json
import os
import gitlab
from fuzzywuzzy import process
import pandas as pd
from dotenv import load_dotenv

from ai_analytics import analyze_queries


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Query Descriptor",
    layout="wide"
)


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv()

GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_PRIVATE_TOKEN = os.getenv("GITLAB_PRIVATE_TOKEN")
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")

if not GITLAB_URL or not GITLAB_PRIVATE_TOKEN or not GITLAB_PROJECT_ID:

    st.error(
        "GitLab configuration is missing. "
        "Please check your .env file."
    )

    st.stop()


try:

    GITLAB_PROJECT_ID = int(GITLAB_PROJECT_ID)

    gl = gitlab.Gitlab(
        GITLAB_URL,
        private_token=GITLAB_PRIVATE_TOKEN
    )

    project = gl.projects.get(
        GITLAB_PROJECT_ID
    )


except Exception as e:

    st.error(
        f"Unable to connect to GitLab: {e}"
    )

    st.stop()


# ============================================================
# FILE & TAG CONFIGURATION
# ============================================================

DATA_FILE = "local_issues.json"
UPLOAD_DIR = "uploads"
CSV_FILE = "issues.csv"

EXCLUDED_TAGS = [
    "solved",
    "auto-tagged",
    "issue"
]

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "search_history" not in st.session_state:

    st.session_state.search_history = []


if "view_history" not in st.session_state:

    st.session_state.view_history = []


# ============================================================
# LOCAL STORAGE FUNCTIONS
# ============================================================

def load_local_issues():

    if os.path.exists(DATA_FILE):

        try:

            with open(
                DATA_FILE,
                "r"
            ) as f:

                return json.load(f)

        except json.JSONDecodeError:

            return []

    return []


def save_local_issue(issue):

    issues = load_local_issues()

    issues.append(issue)

    with open(
        DATA_FILE,
        "w"
    ) as f:

        json.dump(
            issues,
            f,
            indent=4
        )


    # Also save to CSV

    df = pd.DataFrame(
        [issue]
    )


    if os.path.exists(CSV_FILE):

        df.to_csv(
            CSV_FILE,
            mode="a",
            header=False,
            index=False
        )

    else:

        df.to_csv(
            CSV_FILE,
            index=False
        )


# ============================================================
# LOAD LOCAL ISSUES
# ============================================================

if "local_issues" not in st.session_state:

    st.session_state.local_issues = load_local_issues()


# ============================================================
# FETCH GITLAB ISSUES
# ============================================================

try:

    gitlab_issues = project.issues.list(
        all=True
    )

except Exception as e:

    st.error(
        f"Unable to retrieve GitLab issues: {e}"
    )

    gitlab_issues = []


# ============================================================
# TAG FUNCTION
# ============================================================

def get_user_tags():

    local_tags = [

        tag

        for issue
        in st.session_state.local_issues

        for tag
        in issue.get(
            "tags",
            []
        )
    ]


    gitlab_tags = [

        tag

        for issue
        in gitlab_issues

        for tag
        in issue.labels

        if tag.lower()
        not in EXCLUDED_TAGS
    ]


    return local_tags + gitlab_tags


# ============================================================
# MAIN UI
# ============================================================

col1, col2 = st.columns(
    [1, 2]
)


# ============================================================
# LEFT PANEL
# SUBMIT QUERY
# ============================================================

with col1:

    st.markdown(
        "## 🆕 Submit a Query"
    )


    with st.form(
        "complaint_form"
    ):

        title = st.text_input(
            "Title"
        )


        description = st.text_area(
            "Description"
        )


        tags = st.text_input(
            "Tags (comma separated)"
        )


        code = st.text_area(
            "Solution or Experience (Optional)",
            height=150
        )


        uploaded_file = st.file_uploader(
            "Attach Screenshot or Logs",
            type=[
                "png",
                "jpg",
                "jpeg",
                "txt",
                "log"
            ]
        )


        col_gitlab, col_browser = st.columns(
            2
        )


        submit_gitlab = col_gitlab.form_submit_button(
            "📤 Submit to GitLab"
        )


        submit_browser = col_browser.form_submit_button(
            "🌐 Submit to Browser"
        )


        # ====================================================
        # SUBMISSION
        # ====================================================

        if (
            submit_gitlab
            or submit_browser
        ) and title and description:


            file_name = ""


            # ------------------------------------------------
            # SAVE UPLOADED FILE
            # ------------------------------------------------

            if uploaded_file:

                file_name = uploaded_file.name

                file_path = os.path.join(
                    UPLOAD_DIR,
                    file_name
                )


                with open(
                    file_path,
                    "wb"
                ) as f:

                    f.write(
                        uploaded_file.getbuffer()
                    )


            # ------------------------------------------------
            # CREATE ISSUE OBJECT
            # ------------------------------------------------

            issue_data = {

                "title": title,

                "description":
                    description
                    +
                    (
                        "\n\nCode:\n"
                        + code
                        if code
                        else ""
                    ),

                "tags": [

                    t.strip()

                    for t
                    in tags.split(",")

                    if t.strip()
                ],

                "timestamp":
                    datetime.datetime.now().isoformat(),

                "file":
                    file_name
            }


            # ------------------------------------------------
            # LOCAL SUBMISSION
            # ------------------------------------------------

            if submit_browser:

                save_local_issue(
                    issue_data
                )


                # Update session state
                st.session_state.local_issues = (
                    load_local_issues()
                )


                st.success(
                    "✅ Query saved locally!"
                )


            # ------------------------------------------------
            # GITLAB SUBMISSION
            # ------------------------------------------------

            if submit_gitlab:

                try:

                    project.issues.create({

                        "title":
                            issue_data["title"],

                        "description":
                            issue_data["description"],

                        "labels":
                            issue_data["tags"]
                    })


                    st.success(
                        "✅ Query submitted to GitLab!"
                    )


                except Exception as e:

                    st.error(
                        f"GitLab submission failed: {e}"
                    )


# ============================================================
# RIGHT PANEL
# SEARCH & QUERY BOARD
# ============================================================

with col2:

    st.title(
        "🔍 Resolved Queries Board"
    )


    query = st.text_input(
        "Search complaints by tag, title or text"
    )


    results = []
    local_results = []


    # ========================================================
    # SEARCH
    # ========================================================

    if query:

        st.session_state.search_history.append(
            query
        )


        # ----------------------------------------------------
        # GITLAB SEARCH
        # ----------------------------------------------------

        for issue in gitlab_issues:

            issue_text = (

                issue.title
                +
                " "
                +
                (
                    issue.description
                    or ""
                )

            ).lower()


            labels = [

                t.lower()

                for t
                in issue.labels
            ]


            # ------------------------------------------------
            # EXACT / SUBSTRING SEARCH
            # ------------------------------------------------

            if (

                query.lower()
                in issue_text

                or

                query.lower()
                in labels

            ):

                results.append(
                    issue
                )


            # ------------------------------------------------
            # FUZZY SEARCH
            # ------------------------------------------------

            else:

                fuzzy_result = process.extractOne(

                    query,

                    [
                        issue.title,
                        issue.description
                        or ""
                    ]
                )


                if (

                    fuzzy_result

                    and

                    fuzzy_result[1] > 80

                ):

                    results.append(
                        issue
                    )


        # ----------------------------------------------------
        # LOCAL SEARCH
        # ----------------------------------------------------

        local_results = [

            issue

            for issue
            in st.session_state.local_issues

            if

            query.lower()
            in issue["title"].lower()

            or

            query.lower()
            in issue["description"].lower()

            or

            query.lower()
            in [

                tag.lower()

                for tag
                in issue.get(
                    "tags",
                    []
                )
            ]
        ]


    # ========================================================
    # IMPORTANT:
    # NO DEFAULT DISPLAY
    # ========================================================
    #
    # Previously:
    #
    # results = gitlab_issues[:5]
    # local_results = local_issues[-5:]
    #
    # That caused submitted queries to appear automatically.
    #
    # Now results remain empty until the user searches.
    # ========================================================


    # ========================================================
    # DISPLAY SEARCH RESULTS
    # ========================================================

    if query:

        if results or local_results:


            # ------------------------------------------------
            # GITLAB RESULTS
            # ------------------------------------------------

            for issue in results:

                st.session_state.view_history.append(
                    issue.title
                )


                with st.expander(
                    f"🔗 {issue.title}"
                ):

                    st.write(
                        issue.description
                    )


                    if issue.labels:

                        st.markdown(
                            "*Tags:* "
                            +
                            ", ".join(
                                issue.labels
                            )
                        )


                    if st.button(

                        f"Delete '{issue.title}' from GitLab",

                        key=f"del_gitlab_{issue.id}"

                    ):

                        try:

                            issue.delete()


                            st.success(
                                f"Issue '{issue.title}' "
                                "deleted from GitLab."
                            )


                            st.rerun()


                        except Exception as e:

                            st.error(
                                f"Failed to delete GitLab issue: {e}"
                            )


            # ------------------------------------------------
            # LOCAL RESULTS
            # ------------------------------------------------

            for issue in local_results:

                st.session_state.view_history.append(
                    issue["title"]
                )


                with st.expander(
                    f"📝 {issue['title']}"
                ):

                    st.write(
                        issue["description"]
                    )


                    if issue.get("tags"):

                        st.markdown(
                            "*Tags:* "
                            +
                            ", ".join(
                                issue["tags"]
                            )
                        )


                    if st.button(

                        f"Delete '{issue['title']}'",

                        key=f"del_local_{issue['timestamp']}"

                    ):

                        # ------------------------------------
                        # REMOVE FROM SESSION STATE
                        # ------------------------------------

                        st.session_state.local_issues = [

                            i

                            for i
                            in st.session_state.local_issues

                            if

                            i["timestamp"]
                            != issue["timestamp"]
                        ]


                        # ------------------------------------
                        # UPDATE JSON
                        # ------------------------------------

                        with open(
                            DATA_FILE,
                            "w"
                        ) as f:

                            json.dump(

                                st.session_state.local_issues,

                                f,

                                indent=4
                            )


                        # ------------------------------------
                        # UPDATE CSV
                        # ------------------------------------

                        if os.path.exists(
                            CSV_FILE
                        ):

                            df = pd.read_csv(
                                CSV_FILE
                            )


                            df = df[

                                df["timestamp"]
                                != issue["timestamp"]
                            ]


                            df.to_csv(

                                CSV_FILE,

                                index=False
                            )


                        st.success(
                            f"Issue '{issue['title']}' "
                            "deleted locally!"
                        )


                        st.rerun()


        else:

            st.info(
                "No matching complaints found."
            )


    else:

        st.info(
            "Enter a search term above to find submitted queries."
        )


    # ========================================================
    # TRENDING TAGS
    # ========================================================

    st.markdown("---")


    all_tags = [

        tag

        for issue
        in gitlab_issues

        for tag
        in issue.labels

        if tag.lower()
        not in EXCLUDED_TAGS

    ] + [

        tag

        for issue
        in st.session_state.local_issues

        for tag
        in issue.get(
            "tags",
            []
        )
    ]


    trending_tags = sorted(

        set(all_tags),

        key=lambda x:
            -all_tags.count(x)

    )[:10]


    if trending_tags:

        st.markdown(
            "### 🔥 Trending Tags"
        )


        st.markdown(

            ", ".join(

                [

                    f"`{tag}`"

                    for tag
                    in trending_tags

                ]
            )
        )


# ============================================================
# AI QUERY ANALYTICS
# ============================================================

st.markdown("---")

st.subheader(
    "🤖 AI-Powered Query Analytics"
)


st.write(
    "Uses semantic embeddings and clustering to identify "
    "recurring topics across submitted queries."
)


# ============================================================
# COMBINE GITLAB AND LOCAL QUERIES
# ============================================================

ai_records = []


# ------------------------------------------------------------
# GITLAB ISSUES
# ------------------------------------------------------------

try:

    gitlab_issues_for_ai = project.issues.list(
        all=True
    )


    for issue in gitlab_issues_for_ai:

        ai_records.append({

            "title":
                issue.title,

            "description":
                issue.description
                or "",

            "source":
                "GitLab"
        })


except Exception:

    gitlab_issues_for_ai = []


# ------------------------------------------------------------
# LOCAL ISSUES
# ------------------------------------------------------------

try:

    if os.path.exists(
        DATA_FILE
    ):

        with open(
            DATA_FILE,
            "r"
        ) as f:

            local_data = json.load(f)


        if isinstance(
            local_data,
            list
        ):

            for item in local_data:

                ai_records.append({

                    "title":
                        item.get(
                            "title",
                            ""
                        ),

                    "description":
                        item.get(
                            "description",
                            ""
                        ),

                    "source":
                        "Local"
                })


except Exception:

    pass


# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

unique_records = []

seen = set()


for record in ai_records:

    key = (

        record["title"]
        .strip()
        .lower(),

        record["description"]
        .strip()
        .lower()
    )


    if key not in seen:

        seen.add(
            key
        )

        unique_records.append(
            record
        )


st.write(
    f"**Queries available for analysis:** "
    f"{len(unique_records)}"
)


# ============================================================
# AI ANALYSIS
# ============================================================

if len(unique_records) >= 2:

    if st.button(
        "🔍 Analyze Query Patterns"
    ):

        with st.spinner(
            "Analyzing query patterns..."
        ):

            analyzed_df = analyze_queries(

                unique_records,

                n_clusters=4
            )


        if analyzed_df.empty:

            st.warning(
                "Not enough usable query text for analysis."
            )


        else:

            # ==================================================
            # OVERALL SUMMARY
            # ==================================================

            total_queries = len(
                analyzed_df
            )


            total_topics = (
                analyzed_df[
                    "cluster"
                ]
                .nunique()
            )


            st.markdown(
                "### 📊 Overall Query Overview"
            )


            col1, col2 = st.columns(
                2
            )


            with col1:

                st.metric(
                    "Total Queries",
                    total_queries
                )


            with col2:

                st.metric(
                    "Recurring Topics",
                    total_topics
                )


            # ==================================================
            # TOPIC SUMMARY
            # ==================================================

            st.markdown(
                "### 🧠 Recurring Query Topics"
            )


            cluster_summary = (

                analyzed_df

                .groupby(
                    [
                        "cluster",
                        "cluster_name"
                    ],
                    as_index=False
                )

                .agg(
                    query_count=(
                        "title",
                        "count"
                    )
                )

                .sort_values(
                    "query_count",
                    ascending=False
                )
            )


            cluster_summary[
                "percentage"
            ] = (

                cluster_summary[
                    "query_count"
                ]

                /

                total_queries

                *

                100

            ).round(1)


            # ==================================================
            # DISPLAY EACH TOPIC
            # ==================================================

            for _, row in cluster_summary.iterrows():

                cluster_id = row[
                    "cluster"
                ]


                cluster_rows = analyzed_df[

                    analyzed_df[
                        "cluster"
                    ]

                    ==

                    cluster_id
                ]


                keywords = cluster_rows[

                    "cluster_keywords"

                ].iloc[0]


                st.markdown(

                    f"#### 🔹 "
                    f"{row['cluster_name']}"

                )


                col1, col2, col3 = st.columns(
                    3
                )


                with col1:

                    st.metric(

                        "Queries",

                        int(
                            row[
                                "query_count"
                            ]
                        )
                    )


                with col2:

                    st.metric(

                        "Share",

                        f"{row['percentage']}%"
                    )


                with col3:

                    st.write(

                        f"**Keywords:** "
                        f"{keywords}"
                    )


                # ------------------------------------------------
                # ACTUAL QUERIES
                # ------------------------------------------------

                with st.expander(

                    f"View "
                    f"{int(row['query_count'])} "
                    f"queries"

                ):

                    for _, query_row in cluster_rows.iterrows():

                        st.markdown(

                            f"**{query_row['title']}**"
                        )


                        if query_row[
                            "description"
                        ]:

                            description = query_row[
                                "description"
                            ]


                            if len(
                                description
                            ) > 250:

                                description = (

                                    description[:250]

                                    + "..."
                                )


                            st.caption(
                                description
                            )


                        st.caption(

                            f"Source: "
                            f"{query_row['source']}"
                        )


                        st.divider()


            # ==================================================
            # MOST COMMON TOPIC
            # ==================================================

            top_cluster = (
                cluster_summary.iloc[0]
            )


            st.success(

                f"Most common recurring topic: "

                f"**{top_cluster['cluster_name']}** "

                f"("
                f"{int(top_cluster['query_count'])}"
                f" queries, "

                f"{top_cluster['percentage']}%"
                f" of analyzed queries)"
            )


else:

    st.info(
        "Add at least 2 queries before running AI analytics."
    )
