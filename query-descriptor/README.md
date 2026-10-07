# Query Descriptor

A lightweight query and complaint management platform built with **Streamlit** that helps users log technical queries, manage issues through **GitLab**, search existing queries, and identify recurring problem patterns using **AI-powered semantic clustering**.

## 📌 Problem Statement

Technical queries and complaints can become scattered across different discussions and issue threads, making it difficult for teams to:

* Find previously reported problems
* Search for similar queries when wording differs
* Track frequently occurring issues
* Identify recurring problem areas across multiple queries

**Query Descriptor** provides a centralized platform for managing these queries and extracting useful insights from them.

## 💡 Solution

The application allows users to:

* Submit and manage technical queries
* Create GitLab issues directly from the application
* Store queries locally using JSON/CSV
* Search queries using keyword and fuzzy matching
* Track search and query-view activity
* Identify trending tags
* Analyze recurring query patterns embeddings and K-Means clustering

The AI analytics feature extends traditional keyword-based search by identifying queries that are **semantically similar even when they use different wording**.

---

## ✨ Features

### 1. Query Management

Users can submit queries with:

* Title
* Description
* Tags
* Optional solution/experience
* Optional screenshots or log files

Queries can either be stored locally or submitted directly as GitLab issues.

### 2. GitLab Integration

The application integrates with GitLab through the **GitLab REST API** using the `python-gitlab` library.

Supported operations include:

* Retrieve GitLab issues
* Create new issues
* Delete existing issues

This allows Query Descriptor to work as a lightweight interface for managing project-related GitLab issues.

### 3. Query Search

The application provides two levels of search:

**Keyword-based search**

Matches queries based on:

* Title
* Description
* Tags

**Fuzzy search**

Uses FuzzyWuzzy to identify queries with similar wording, helping users find relevant results even when the search text is not an exact match.

> Fuzzy matching is an algorithmic string-similarity technique, not a machine-learning model.

### 4. Trending Tags & Analytics

The application tracks query-related activity and provides:

* Trending tags
* Top searches
* Frequently viewed queries

st.session_state is used to maintain session-level search and view history across Streamlit reruns.

### 5. AI-Powered Query Analytics

The project includes an AI-based analytics module for discovering recurring problem patterns.

The pipeline is:


Query Title + Description
          ↓
Sentence Transformer
(all-MiniLM-L6-v2)
          ↓
Semantic Embedding
          ↓
K-Means Clustering
          ↓
Recurring Query Groups


The pretrained ** all-MiniLM-L6-v2 ** model converts query text into semantic embeddings.

These embeddings are then clustered using **K-Means**, an unsupervised machine-learning algorithm.

For example:


"Unable to login to my account"
"My credentials are rejected"
"I cannot sign into the application"
              ↓
      Similar embeddings
              ↓
       Same cluster
              ↓
   Recurring problem area


This helps the team identify repeated issues even when users describe them using different words.

---

## 🧠 Machine Learning Approach

### Sentence Embeddings

The project uses:

**Model:** `all-MiniLM-L6-v2`

It is a pretrained Sentence Transformer model used to generate semantic representations of text.

The query title and description are combined and converted into a numerical embedding.


Text
 ↓
Tokenization
 ↓
Transformer
 ↓
Contextual representations
 ↓
Pooling
 ↓
384-dimensional sentence embedding


The resulting embeddings allow queries to be represented mathematically and compared based on their semantic relationships.

### K-Means Clustering

K-Means is used because the query data does not have predefined categories or labels.

The algorithm:

1. Initializes cluster centroids
2. Assigns embeddings to the nearest centroid
3. Recalculates the centroids
4. Reassigns embeddings
5. Repeats until the clusters stabilize

The current implementation uses a small number of clusters to keep the results lightweight and interpretable.

For a production system, the number of clusters could be evaluated using methods such as the **Elbow Method** or **Silhouette Score**.

---

## 🏗️ System Architecture

`
                    User
                      │
                      ↓
                Streamlit UI
                      │
                      ↓
              Python Application
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   Local Storage    Search       Analytics
   JSON / CSV       │             │
                    ↓             ↓
               FuzzyWuzzy     Pandas /
                              Matplotlib
                      │
                      │
                      ↓
              GitLab Integration
                      │
                python-gitlab
                      │
                      ↓
                 GitLab REST API
                      │
                      ↓
                GitLab Issues

'
              AI Analytics Pipeline
                      │
                      ↓
             Query Title + Description
                      │
                      ↓
          all-MiniLM-L6-v2
                      │
                      ↓
          Semantic Embeddings
                      │
                      ↓
                  K-Means
                      │
                      ↓
             Query Clusters


---

## 🛠️ Technology Stack

### Frontend / Application

* **Python**
* **Streamlit**

### API Integration

* **python-gitlab**
* **GitLab REST API**

### Data Handling

* **Pandas**
* **JSON**
* **CSV**

### Search

* **FuzzyWuzzy**
* Keyword-based matching

### Machine Learning

* **Sentence Transformers**
* **all-MiniLM-L6-v2**
* **Scikit-learn**
* **K-Means Clustering**

### Visualization

* **Matplotlib**

### Configuration

* **python-dotenv**

---

## 📂 Project Structure


Query-Descriptor/
│
├── app.py
├── ai_analytics.py
├── requirements.txt
├── .env
├── .gitignore
│
├── uploads/
│
├── local_issues.json
└── issues.csv


### File Description

| File                | Purpose                                         |
| ------------------- | ----------------------------------------------- |
|  app.py             | Main Streamlit application                      |
|  ai_analytics.py    | Semantic embedding and K-Means clustering logic |
|  requirements.txt   | Python dependencies                             |
|  .env               | GitLab configuration and credentials            |
| local_issues.json   | Local query storage                             |
|  issues.csv         | Tabular representation of local queries         |
| uploads/            | Stores uploaded screenshots/log files           |

---

## ⚙️ Installation

### 1. Clone the repository


git clone <your-repository-url>
cd Query-Descriptor


### 2. Create a virtual environment


python -m venv venv


Activate it on Windows:


venv\Scripts\activate


### 3. Install dependencies


pip install -r requirements.txt


### 4. Configure GitLab credentials

Create a `.env` file:


GITLAB_URL=https://your-gitlab-instance/
GITLAB_PRIVATE_TOKEN=your_token_here
GITLAB_PROJECT_ID=your_project_id


**Do not commit `.env` or expose your GitLab personal access token.**

### 5. Run the application


streamlit run app.py


The application will open in your browser.

---

## 📦 Requirements

Example requirements.txt :


streamlit
python-gitlab
fuzzywuzzy
pandas
matplotlib
python-dotenv
sentence-transformers
scikit-learn


---

## 🔐 Security

Sensitive credentials should be stored outside the source code.

Recommended:


.env


and included in:


.gitignore


Example:


.env
__pycache__/
*.pyc
uploads/
local_issues.json
issues.csv
.streamlit/secrets.toml


Never commit GitLab personal access tokens to a public repository.

---

## 📊 Data Flow

When a user submits a query to GitLab:


User
 ↓
Streamlit Form
 ↓
Python Application
 ↓
python-gitlab
 ↓
GitLab REST API
 ↓
GitLab Project
 ↓
Issue Created


For AI analytics:


GitLab Issues + Local Queries
              ↓
       Query Collection
              ↓
      Title + Description
              ↓
   all-MiniLM-L6-v2
              ↓
     Semantic Embeddings
              ↓
          K-Means
              ↓
       Query Clusters
              ↓
Recurring Problem Patterns


---

## 🎯 Business Impact

Query Descriptor is designed to move beyond simply storing and resolving individual queries.

It provides teams with:

* **Centralized query management**
* **Faster discovery of existing issues**
* **Improved visibility into frequently occurring problems**
* **Semantic grouping of differently worded queries**
* **Data-driven identification of recurring problem areas**
* **Better opportunities for prioritization and documentation**

The AI analytics component particularly helps transform raw query data into **actionable problem-pattern insights**.

---

## 🚀 Future Improvements

Potential improvements include:

* Automatic cluster labeling
* Automatic query categorization
* Better persistent database storage
* Advanced full-text/semantic search
* Pagination for large GitLab projects
* More robust API error handling
* Authentication and role-based access
* File validation and secure upload handling
* Automatic cluster-quality evaluation
* Interactive AI analytics dashboards

##

##
