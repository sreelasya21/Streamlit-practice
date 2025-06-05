import streamlit as st
import datetime
import json
import os
import gitlab
from fuzzywuzzy import process
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

# ------------------- GitLab Configuration -------------------
GITLAB_URL = "https://code.swecha.org/"  # Your GitLab instance URL
GITLAB_PRIVATE_TOKEN = "glpat-mpXX8Za34B4vMr4sn6nx"  # Replace with a valid personal access token
GITLAB_PROJECT_ID = 23954  # Replace with your actual project ID

gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_PRIVATE_TOKEN)
project = gl.projects.get(GITLAB_PROJECT_ID)

# ------------------- File & Tag Setup -------------------
DATA_FILE = "local_issues.json"
UPLOAD_DIR = "uploads"
CSV_FILE = "issues.csv"
EXCLUDED_TAGS = ["solved", "auto-tagged", "issue"]
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Metrics for views and searches
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "view_history" not in st.session_state:
    st.session_state.view_history = []

def load_local_issues():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_local_issue(issue):
    issues = load_local_issues()
    issues.append(issue)
    with open(DATA_FILE, "w") as f:
        json.dump(issues, f)
    # Also save to CSV
    df = pd.DataFrame([issue])
    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)

if "local_issues" not in st.session_state:
    st.session_state.local_issues = load_local_issues()

gitlab_issues = project.issues.list(all=True)

def get_user_tags():
    local_tags = [tag for issue in st.session_state.local_issues for tag in issue.get("tags", [])]
    gitlab_tags = [
        tag for issue in gitlab_issues
        for tag in issue.labels
        if tag.lower() not in EXCLUDED_TAGS
    ]
    return local_tags + gitlab_tags

# ------------------- UI Layout -------------------
st.set_page_config(layout="wide")
col1, col2 = st.columns([1, 2])

# ------------------- LEFT PANEL - New Complaint Form -------------------
with col1:
    st.markdown("## 🆕 Submit a Query")
    with st.form("complaint_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        tags = st.text_input("Tags (comma separated)")
        code = st.text_area("Solution or Experience(Optional)", height=150)
        uploaded_file = st.file_uploader("Attach Screenshot or Logs", type=["png", "jpg", "jpeg", "txt", "log"])

        col_gitlab, col_browser = st.columns(2)
        submit_gitlab = col_gitlab.form_submit_button("📤 Submit to GitLab")
        submit_browser = col_browser.form_submit_button("🌐 Submit to Browser")

        if (submit_gitlab or submit_browser) and title and description:
            file_name = ""
            if uploaded_file:
                file_name = uploaded_file.name
                file_path = os.path.join(UPLOAD_DIR, file_name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())

            issue_data = {
                "title": title,
                "description": description + ("\n\nCode:\n" + code if code else ""),
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
                "timestamp": datetime.datetime.now().isoformat(),
                "file": file_name
            }

            if submit_browser:
                save_local_issue(issue_data)
                st.success("✅ Complaint saved to browser!")

            if submit_gitlab:
                created = project.issues.create({
                    "title": issue_data["title"],
                    "description": issue_data["description"],
                    "labels": issue_data["tags"]
                })
                st.success("✅ Complaint submitted to GitLab!")

# ------------------- RIGHT PANEL - View/Search Complaints -------------------
with col2:
    st.title("🔍 Resolved Queries Board")
    query = st.text_input("Search complaints by tag, title or text")

    results = []
    if query:
        st.session_state.search_history.append(query)
        for issue in gitlab_issues:
            if query.lower() in (issue.title + " " + (issue.description or "")).lower() or \
               query.lower() in [t.lower() for t in issue.labels]:
                results.append(issue)
            elif process.extractOne(query, [issue.title, issue.description or ""])[1] > 80:
                results.append(issue)

        local_results = [
            issue for issue in st.session_state.local_issues
            if query.lower() in issue["title"].lower() or
               query.lower() in issue["description"].lower() or
               query.lower() in [tag.lower() for tag in issue.get("tags", [])]
        ]
    else:
        results = gitlab_issues[:5]
        local_results = st.session_state.local_issues[-5:]

    if results or local_results:
        for issue in results:
            st.session_state.view_history.append(issue.title)
            with st.expander(f"🔗 {issue.title}"):
                st.write(issue.description)
                if issue.labels:
                    st.markdown("*Tags:* " + ", ".join(issue.labels))

                # Delete button for GitLab issue
                if st.button(f"Delete '{issue.title}' from GitLab", key=f"del_gitlab_{issue.id}"):
                    try:
                        issue.delete()
                        st.success(f"Issue '{issue.title}' deleted from GitLab.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to delete GitLab issue: {e}")

        for issue in local_results:
            st.session_state.view_history.append(issue['title'])
            with st.expander(f"📝 {issue['title']}"):
                st.write(issue["description"])
                if issue.get("tags"):
                    st.markdown("*Tags:* " + ", ".join(issue["tags"]))

                # Delete button for local issue
                if st.button(f"Delete '{issue['title']}'", key=f"del_local_{issue['timestamp']}"):
                    # Remove from session state list
                    st.session_state.local_issues = [i for i in st.session_state.local_issues if i["timestamp"] != issue["timestamp"]]

                    # Update local JSON file
                    with open(DATA_FILE, "w") as f:
                        json.dump(st.session_state.local_issues, f)

                    # Remove from CSV file
                    if os.path.exists(CSV_FILE):
                        df = pd.read_csv(CSV_FILE)
                        # Assuming 'timestamp' column exists in CSV and is unique identifier
                        df = df[df['timestamp'] != issue['timestamp']]
                        df.to_csv(CSV_FILE, index=False)

                    st.success(f"Issue '{issue['title']}' deleted locally!")
                    st.experimental_rerun()

    else:
        st.info("No matching complaints found.")

    # Trending Tags
    st.markdown("---")
    all_tags = [
        tag for issue in gitlab_issues for tag in issue.labels if tag.lower() not in EXCLUDED_TAGS
    ] + [tag for issue in st.session_state.local_issues for tag in issue.get("tags", [])]
    trending_tags = sorted(set(all_tags), key=lambda x: -all_tags.count(x))[:10]
    if trending_tags:
        st.markdown("### 🔥 Trending Tags")
        st.markdown(", ".join([f"`{tag}`" for tag in trending_tags]))

    # Top 5 Searches and Views
    st.markdown("---")
    st.markdown("### 📊 Top Search & View Stats")
    col_search, col_view = st.columns(2)

    with col_search:
        st.markdown("#### 🔍 Top 5 Searches")
        if st.session_state.search_history:
            search_counts = Counter(st.session_state.search_history)
            top_searches = search_counts.most_common(5)
            fig1, ax1 = plt.subplots()
            ax1.bar([x[0] for x in top_searches], [x[1] for x in top_searches], color='skyblue')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig1)
        else:
            st.write("No searches yet.")

    with col_view:
        st.markdown("#### 👁️ Top 5 Views")
        if st.session_state.view_history:
            view_counts = Counter(st.session_state.view_history)
            top_views = view_counts.most_common(5)
            fig2, ax2 = plt.subplots()
            ax2.bar([x[0] for x in top_views], [x[1] for x in top_views], color='orange')
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)
        else:
            st.write("No views yet.")
