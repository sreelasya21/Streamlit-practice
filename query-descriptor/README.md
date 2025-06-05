# 🛠️ Streamlit Complaint Management System with GitLab Integration

This is a lightweight complaint/query management web app built with **Streamlit** that allows users to:
- 📝 Submit queries locally (browser) or to a GitLab project as issues.
- 🔍 Search and browse all submitted queries with fuzzy matching.
- 📊 View analytics like top searches and views.
- 📌 See trending tags from all issues.
- ❌ Delete complaints from both browser (JSON/CSV) and GitLab.

---

## 🚀 Features

- Submit complaints with:
  - Title, description, tags
  - Optional code snippets and file attachments
- Submit to:
  - 🌐 Browser (saved in JSON and CSV locally)
  - 📤 GitLab issues
- Search using:
  - Exact or fuzzy matches on title, description, and tags
- Visualizations:
  - Top 5 searches and views (bar charts)
  - Trending tags
- Delete button for each complaint (both local and GitLab)
- Auto-clear form fields after successful submission

---

## 🧩 Tech Stack

- [Streamlit](https://streamlit.io/)
- [GitLab Python API](https://python-gitlab.readthedocs.io/en/stable/)
- `pandas`, `matplotlib`, `fuzzywuzzy`
- Local storage via `JSON` and `CSV`

---

## ⚙️ Setup Instructions

### 🔧 Prerequisites

- Python 3.8+
- A GitLab account and [Personal Access Token](https://code.swecha.org/-/profile/personal_access_tokens)
- GitLab project where issues will be submitted

### 📁 Installation

```bash
git clone https://code.swecha.org/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
