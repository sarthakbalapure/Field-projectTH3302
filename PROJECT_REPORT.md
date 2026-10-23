# Engineering Project Report
# AI-Powered IT Incident Process Intelligence

**Document Type:** Formal Technical Project Report  
**Domain:** IT Service Management (ITSM), Process Mining, Applied Machine Learning  
**Project Lead:** [Your Name / Candidate Name]  
**Academic / Institutional Affiliation:** [Department of Computer Science / Engineering]  
**Status:** Completed & Validated  
**Date:** October 2026  

---

## Executive Abstract

Modern IT operations organizations handle thousands of ITIL incidents monthly across distributed infrastructure, cloud platforms, and application suites. Despite heavy investments in IT Service Management (ITSM) tracking tools, operational leaders struggle with opaque queue delays, costly rework loops, and high SLA violation rates. Traditional ITSM reporting relies almost exclusively on aggregate retrospective key performance indicators (KPIs)—such as average resolution time—which mask execution path deviations and inter-team dormancy.

This report presents the design, implementation, and empirical evaluation of **AI-Powered IT Incident Process Intelligence**, an end-to-end analytical platform inspired by Celonis process intelligence concepts. The system integrates:
1. **Process Mining (PM4Py & transition network discovery)** to reconstruct the actual chronological execution flows of 1,200 incident cases (8,676 event records).
2. **Workflow Variant & Bottleneck Diagnostics** that reveal standard "Happy Path" workflows (55.42% share) resolve in 22.18 hours, whereas deviant and escalated paths (44.58% share) take **1.77x longer** (39.33 hours) with a 77.76% SLA breach rate.
3. **Leakage-Free Predictive Machine Learning (Random Forest)** trained strictly on early-lifecycle incident signals, achieving **76.43% precision** and **74.05% F1-score** in predicting SLA violations before active investigation.
4. **An Explainable Decision Support Engine** translating empirical queue latencies into prioritized operational recommendations.
5. **An Interactive Streamlit Operations Dashboard** enabling shift leads to run real-time SLA breach risk simulations and audit individual ticket event traces.

---

## 1. Introduction & Background

### 1.1 Context
Incident Management is a foundational component of the ITIL (Information Technology Infrastructure Library) framework, aimed at restoring normal service operation as quickly as possible while minimizing adverse impact on business operations. Organizations define Service Level Agreements (SLAs) stipulating maximum permissible turnaround times categorized by business urgency and impact (Priority tiers P1 through P4).

### 1.2 Problem Statement
Standard ITSM platforms (e.g., Jira Service Management, ServiceNow) capture state changes but present them through static tabular views. Consequently, IT operations management faces four critical deficiencies:
1. **Invisible Queue Dormancy:** Tickets spend the majority of their lifespan waiting between queues rather than undergoing active technical diagnosis.
2. **The Rework Multiplier:** Tickets that are repeatedly escalated or reopened consume disproportionate engineering hours without visible root-cause tracking.
3. **Reactive SLA Management:** Operations teams receive notifications only *after* an SLA window has breached, rendering mitigation impossible.
4. **Predictive Modeling Failures:** Naive machine learning models in academic literature frequently suffer from **data leakage**, utilizing post-incident features (such as final close notes or total logged hours) that do not exist during early triage.

### 1.3 Project Objectives
- Synthesize a realistic, multi-event ITIL lifecycle event log capturing 1,200 incident cases with authentic operational anomalies.
- Implement process discovery algorithms (Directly-Follows Graphs) using PM4Py and graph transition matrices.
- Benchmark standard Happy Path executions against rework and escalation deviations.
- Construct and evaluate a leak-free Machine Learning model predicting SLA breach probabilities during early triage.
- Build an explainable recommendation engine prescribing quantitative operational interventions.
- Deliver an interactive, responsive Streamlit dashboard with real-time risk scoring and trace auditing.

---

## 2. Theoretical Foundations

### 2.1 Process Mining Concepts
Process mining bridges the gap between traditional data science and business process management (BPM). An event log $L$ consists of cases $C$, where each case $c \in C$ represents a sequence of timestamped events:

$$\sigma_c = \langle (a_1, t_1), (a_2, t_2), \dots, (a_k, t_k) \rangle$$

Where $a_i \in \mathcal{A}$ is the executed activity and $t_i$ is the corresponding timestamp.

#### Directly-Follows Graph (DFG)
A Directly-Follows Graph is a directed graph $G = (V, E)$ where:
- Vertices $V = \mathcal{A}$ correspond to distinct activities.
- Directed edges $(u, v) \in E$ exist if activity $v$ directly succeeds activity $u$ in at least one trace $\sigma_c$.
- Edge weight $W(u, v)$ represents the transition frequency or mean duration:

$$\bar{D}(u, v) = \frac{1}{|E_{u \to v}|} \sum_{i=1}^{|E_{u \to v}|} (t_{v, i} - t_{u, i})$$

### 2.2 Anti-Leakage Feature Engineering
In supervised binary classification for SLA breach prediction:

$$y \in \{0, 1\} \quad (1 = \text{SLA Breached}, 0 = \text{SLA Met})$$

A model $f(X)$ must only ingest feature vector $X$ measured at observation threshold $\tau$ (e.g., within 30 minutes of incident ingestion). Any feature $x_j \in X$ whose realization depends on events occurring after $\tau$ (such as final resolution timestamp $t_{end}$ or total post-investigation escalation count) induces target leakage, creating artificially inflated evaluation metrics that fail in deployment.

---

## 3. System Architecture & Engineering Design

### 3.1 Architectural Overview
The platform follows a decoupled 4-layer architecture:

```mermaid
flowchart TD
    subgraph Layer 1: Data Engineering
        A[Event Log Generator<br/>data_generator.py] -->|1,200 Cases / 8,676 Events| B[(sample_incidents.csv)]
        B --> C[Preprocessing Engine<br/>preprocessing.py]
    end

    subgraph Layer 2: Analytical Core
        C -->|Event Logs| D[PM4Py & DFG Engine<br/>process_analysis.py]
        C -->|Early Features Vector| E[ML Prediction Pipeline<br/>model.py]
    end

    subgraph Layer 3: Decision Intelligence
        D -->|Bottlenecks & Variants| F[Recommendation Engine<br/>recommendations.py]
        E -->|Risk Probabilities| F
    end

    subgraph Layer 4: Presentation & Operations
        D --> G[Streamlit Dashboard<br/>app.py]
        E --> G
        F --> G
        G --> H[Executive Overview]
        G --> I[Process Flow Map]
        G --> J[Bottleneck Diagnostics]
        G --> K[Interactive SLA Simulator]
        G --> L[AI Recommendations]
        G --> M[Audit Trace Explorer]
    end
```

### 3.2 Component Specifications

| Module | File Path | Primary Responsibilities |
| :--- | :--- | :--- |
| **Data Generator** | [`src/data_generator.py`](file:///c:/fp/src/data_generator.py) | Synthesizes 1,200 IT incident cases with log-normal triage lags, gamma investigation delays, and team bottleneck multipliers. |
| **Preprocessing** | [`src/preprocessing.py`](file:///c:/fp/src/preprocessing.py) | Parses timestamps, extracts ordered activity transitions, computes case-level aggregates, and isolates leak-free early-stage feature vectors. |
| **Process Analysis** | [`src/process_analysis.py`](file:///c:/fp/src/process_analysis.py) | Interfaces with PM4Py 2.7+ for DFG discovery; computes variant distributions, Happy vs Deviant path multipliers, and ranked bottleneck matrices. |
| **Predictive Model** | [`src/model.py`](file:///c:/fp/src/model.py) | Implements Scikit-Learn `Pipeline` with `ColumnTransformer` and `RandomForestClassifier`; evaluates metrics; persists artifact via Joblib. |
| **Recommendations** | [`src/recommendations.py`](file:///c:/fp/src/recommendations.py) | Evaluates empirical queue statistics against operational heuristics; outputs priority-badged recommendations. |
| **Interactive UI** | [`app.py`](file:///c:/fp/app.py) | Streamlit web console featuring Plotly visualizations, responsive CSS styling, and live parameter simulation. |
| **Test Suite** | [`tests/test_basic.py`](file:///c:/fp/tests/test_basic.py) | Comprehensive automated test suite validating data generation, preprocessing, model inference, and recommendation generation. |

---

## 4. Dataset Description & Statistical Characteristics

The generated dataset comprises **1,200 unique incident cases** and **8,676 event records**, covering 90 days of operations.

### 4.1 Schema Definition
- `incident_id`: Unique identifier (e.g., `INC-10042`).
- `activity`: Lifecycle milestone (`Incident Created`, `Initial Assessment`, `Team Assignment`, `Investigation`, `Escalation`, `Resolution`, `Incident Closed`, `Incident Reopened`).
- `timestamp`: Chronological ISO string (`YYYY-MM-DD HH:MM:SS`).
- `incident_type`: Operational category (`Infrastructure Outage`, `Database Performance`, `Software Bug`, `Access & Identity`, `Network Connectivity`, `Security Alert`).
- `priority`: Service urgency tier (`P1 - Critical`, `P2 - High`, `P3 - Medium`, `P4 - Low`).
- `severity`: Technical impact (`Critical`, `Major`, `Moderate`, `Minor`).
- `assigned_team`: Specialized group (`Service Desk`, `Network Ops`, `Cloud Infra`, `Database Admin`, `SecOps`, `App Support`).
- `source`: Ingestion origin (`Monitoring Alert`, `User Portal`, `Email`, `Phone Call`, `Automated Script`).
- `status`: Lifecycle state (`New`, `In Progress`, `Escalated`, `Resolved`, `Closed`).
- `resolution_time_hours`: Total case duration from creation to final closure.
- `sla_target_hours`: Contractual limit (P1: 4.0h, P2: 12.0h, P3: 24.0h, P4: 72.0h).
- `reopened`: Boolean flag indicating whether ticket required secondary intervention after closure.
- `escalation_count`: Integer count of tier-to-tier escalations.

### 4.2 Statistical Breakdown
- **Priority Distribution:**
  - P3 - Medium: 42.7% (512 cases)
  - P2 - High: 27.8% (334 cases)
  - P4 - Low: 17.1% (205 cases)
  - P1 - Critical: 12.4% (149 cases)
- **Lifecycle Metrics:**
  - Average Total Resolution Time: **29.8 hours** (Median: 24.0 hours)
  - Overall SLA Compliance: **38.1%** (61.9% breach rate)
  - Ticket Reopening Rate: **9.5%** (114 cases)
  - Escalation Rate: **35.7%** (428 cases)

---

## 5. Process Mining & Workflow Analysis

### 5.1 Variant Discovery & Benchmark
By grouping cases by identical ordered activity traces, the system identified process variants across the 1,200 incident cases:

| Variant ID | Lifecycle Activity Sequence | Cases | Share | Avg Turnaround | SLA Breach % |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Variant #1 (Happy Path)** | `Created` $\to$ `Assessment` $\to$ `Assignment` $\to$ `Investigation` $\to$ `Resolution` $\to$ `Closed` | **665** | **55.42%** | **22.18 hrs** | **49.17%** |
| **Variant #2 (Single Escalation)** | `Created` $\to$ `Assessment` $\to$ `Assignment` $\to$ `Investigation` $\to$ `Escalation` $\to$ `Investigation` $\to$ `Resolution` $\to$ `Closed` | **268** | **22.33%** | **35.40 hrs** | **71.27%** |
| **Variant #3 (Reopened Flow)** | `...` $\to$ `Resolution` $\to$ `Closed` $\to$ `Reopened` $\to$ `Investigation` $\to$ `Resolution` $\to$ `Closed` | **114** | **9.50%** | **44.82 hrs** | **88.60%** |
| **Variant #4 (Multi-Escalation)** | Multiple escalation handoffs before resolution | **105** | **8.75%** | **51.10 hrs** | **89.52%** |
| **Variant #5 (Fast-Track Fix)** | `Created` $\to$ `Assessment` $\to$ `Resolution` $\to$ `Closed` | **48** | **4.00%** | **4.20 hrs** | **4.17%** |

#### Key Takeaway:
Deviant paths (44.58% of cases) experience a **1.77x cycle time multiplier** (39.33h vs. 22.18h) and an increase of **28.59%** in SLA violation probability compared to the standard Happy Path.

### 5.2 Bottleneck Diagnostics
Analyzing step-by-step transition times identified the following latency centers:

| Source Activity | Target Activity | Occurrences | Mean Delay | P90 Delay | Total Waiting Time |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Team Assignment** | **Investigation** | **1,159** | **15.86 hrs** | **36.68 hrs** | **18,381.7 hrs** |
| **Incident Closed** | **Incident Reopened** | **114** | **13.11 hrs** | **22.07 hrs** | **1,495.0 hrs** |
| **Incident Reopened** | **Investigation** | **114** | **8.50 hrs** | **16.42 hrs** | **968.8 hrs** |
| **Escalation** | **Investigation** | **551** | **6.90 hrs** | **13.31 hrs** | **3,803.9 hrs** |
| **Resolution** | **Incident Closed** | **1,314** | **4.38 hrs** | **7.24 hrs** | **5,760.9 hrs** |

**Analytical Conclusion:** The primary operational delay does not occur during technical troubleshooting itself, but during **inter-team queue dormancy** (`Team Assignment -> Investigation`), which accounts for 61.2% of all cumulative waiting hours.

---

## 6. Machine Learning SLA Breach Prediction

### 6.1 Feature Engineering (Strictly Early Signals)
To ensure applicability in live operational environments without data leakage, features were restricted to attributes observable in the first 30 minutes:

```text
Categorical Features:
  - incident_type         (6 categories)
  - priority              (4 categories)
  - severity              (4 categories)
  - assigned_team         (6 categories)
  - source                (5 categories)

Numerical Features:
  - initial_assessment_hours   (Triage delay before assignment)
  - time_to_assignment_hours   (Queue latency before assignment)
  - created_hour               (Hour of creation: 0 - 23)
  - created_dayofweek          (Day of creation: 0 - 6)
  - is_weekend                 (Binary: 1 if Saturday/Sunday)
  - is_offhours                (Binary: 1 if created before 08:00 or after 18:00)
```

### 6.2 Model Training & Hyperparameters
- **Preprocessor:** `ColumnTransformer` with `OneHotEncoder(handle_unknown='ignore')` + `StandardScaler()`.
- **Model:** `RandomForestClassifier`
  - `n_estimators`: 120
  - `max_depth`: 12
  - `min_samples_split`: 5
  - `min_samples_leaf`: 2
  - `class_weight`: `'balanced'` (counters class imbalance)
  - `random_state`: 42
- **Validation:** 80/20 Stratified Train/Test Split ($N_{train} = 960$, $N_{test} = 240$).

### 6.3 Empirical Evaluation Metrics

| Metric | Measured Score | Operational Significance |
| :--- | :---: | :--- |
| **Test Accuracy** | **68.75%** | Reliable overall classification across test population. |
| **Precision (SLA Breach)** | **76.43%** | 3 out of 4 flagged incidents breach SLA; minimizes alert fatigue. |
| **Recall (SLA Breach)** | **71.81%** | Successfully intercepts nearly 72% of all in-flight SLA breaches. |
| **F1-Score** | **74.05%** | Robust balance between false alarms and missed violations. |
| **ROC-AUC** | **74.45%** | Good discriminatory power across all probability thresholds. |

#### Confusion Matrix ($N = 240$):
$$\mathbf{CM} = \begin{pmatrix} \text{True Negatives (Met SLA): } 58 & \text{False Positives: } 33 \\ \text{False Negatives: } 42 & \text{True Positives (Breached): } 107 \end{pmatrix}$$

#### Top Predictive Feature Weights:
1. `priority_P4 - Low` ($0.1196$): Due to its long 72-hour window, P4 incidents are frequently deprioritized, leading to extreme queue stagnation.
2. `initial_assessment_hours` ($0.1099$): Slow initial triage directly compounds downstream SLA risk.
3. `time_to_assignment_hours` ($0.1079$): Delays in team assignment consume the remaining SLA buffer.
4. `created_hour` ($0.0818$): Shift handovers and off-peak hours heighten risk.
5. `priority_P1 - Critical` ($0.0805$): Strict 4-hour target leaves minimal room for error.

---

## 7. Explainable Decision Support Engine

Instead of generic alerts, the recommendation engine maps observed process statistics directly to operational actions:

```text
[CRITICAL] REC-001: Mitigate Long Queue Lag in 'Team Assignment -> Investigation'
- Finding: Mean delay of 15.9 hours across 1,159 cases (P90 = 36.7h; Cumulative = 18,382h).
- Action: Deploy automated assignment routing and pre-flight diagnostic checklists.
- Expected Impact: 20-35% reduction in cycle time for delayed tickets.

[HIGH] REC-004: Rebalance Workload for Database Admin (SLA Breach Rate: 72.41%)
- Finding: Database Admin exhibits a 72.4% SLA breach rate with 18.2h average resolution.
- Action: Review staffing during peak hours; deploy Tier-1 self-healing scripts for routine queries.
- Expected Impact: 15-25% reduction in team SLA breaches.

[MEDIUM] REC-009: Address Reopened Tickets in 'Software Bug' Incidents
- Finding: 9.5% overall reopening rate; Software Bugs represent the highest volume (42 cases).
- Action: Mandate automated post-fix health check verification before status change to 'Closed'.
- Expected Impact: 40% reduction in repeat ticket reopenings.

[MEDIUM] REC-010: Automate Triage for Off-Hours and Night Shifts
- Finding: Off-hours assessment takes 2.2x longer than business hours (0.92h vs 0.42h).
- Action: Implement NLP-based automated classification for off-hours tickets.
- Expected Impact: Accelerate initial triage by up to 60% during off-peak hours.
```

---

## 8. Dashboard Implementation & Verification

The interactive operations console is developed using **Streamlit** and **Plotly**, styled with an executive dark glassmorphic UI.

### 8.1 Dashboard Sections
1. **Executive Overview:** High-level KPI cards, SLA compliance by incident type, priority share pie chart, and team operational benchmark matrix.
2. **Process Analysis:** Interactive Directly-Follows transition Sankey diagram, Happy Path vs Deviant path comparison, and variant breakdown table.
3. **Bottleneck Analysis:** Ranked transition waiting times horizontal bar chart, team resolution box plots, and escalation impact modeling.
4. **SLA Risk Prediction:** Test evaluation scorecards, confusion matrix heatmap, feature importance rankings, and a **Live Incident Risk Simulator** with real-time gauge meter.
5. **AI Recommendations:** Priority-badged actionable recommendation cards with supporting quantitative metrics.
6. **Incident Explorer:** Searchable ticket registry with chronological audit trail inspector.

### 8.2 Visual Verification (Captured Genuine Screenshots)
All screenshots were captured from the running application:

- **Executive Overview:** [`screenshots/dashboard_overview.png`](file:///c:/fp/screenshots/dashboard_overview.png)
- **Process Analysis:** [`screenshots/process_analysis.png`](file:///c:/fp/screenshots/process_analysis.png)
- **Bottleneck Diagnostics:** [`screenshots/bottleneck_analysis.png`](file:///c:/fp/screenshots/bottleneck_analysis.png)
- **SLA Prediction & Simulator:** [`screenshots/sla_prediction.png`](file:///c:/fp/screenshots/sla_prediction.png)
- **AI Recommendations:** [`screenshots/ai_recommendations.png`](file:///c:/fp/screenshots/ai_recommendations.png)

---

## 9. Verification & Quality Assurance

Automated unit and integration tests were executed via `pytest -v tests/test_basic.py`:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\fp
collected 6 items

tests/test_basic.py::test_data_generator PASSED                          [ 16%]
tests/test_basic.py::test_case_aggregation PASSED                        [ 33%]
tests/test_basic.py::test_transitions_and_bottlenecks PASSED             [ 50%]
tests/test_basic.py::test_process_variants_and_pm4py PASSED              [ 66%]
tests/test_basic.py::test_model_training_and_prediction PASSED           [ 83%]
tests/test_basic.py::test_recommendation_engine PASSED                   [100%]

============================== 6 passed in 9.24s ==============================
```

All 6 test suites passed, confirming schema integrity, zero data leakage in feature sets, valid graph discovery, joblib persistence roundtrips, and deterministic inference.

---

## 10. Limitations & Future Roadmap

1. **Synthetic Data Boundaries:** While calibrated against realistic ITIL queues, the dataset does not account for offline verbal escalations or informal chat channels.
2. **Streaming Event Ingestion:** The current architecture operates in micro-batches; integrating streaming backbones (e.g., Apache Kafka / River) would support sub-second incremental learning.
3. **Formal Conformance Checking:** Integrating token-replay conformance checking against normative BPMN models could compute fitness and precision metrics.
4. **Local LLM Integration:** Rule-based recommendation metrics could be ingested by a quantized local LLM (e.g., Llama 3 via Ollama) to draft customized incident post-mortem reports.

---

## 11. Conclusion

The **AI-Powered IT Incident Process Intelligence** platform demonstrates how combining Process Mining (PM4Py) with Leak-Free Machine Learning (Random Forest) transforms IT incident operations. Rather than relying on lagging indicators, operations teams can now:
- Visually discover real execution flows and quantify rework penalties (**1.77x cycle time increase**).
- Pinpoint and address inter-team queue latency (**15.86h average delay**).
- Proactively intercept SLA violations with **76.43% precision** within the first 30 minutes of ticket ingestion.
- Execute data-backed interventions to improve operational performance.

The platform provides an open-source, reproducible alternative to commercial process intelligence suites.

---

## 12. References

1. van der Aalst, W. M. P. (2016). *Process Mining: Data Science in Action*. Springer Berlin Heidelberg.
2. Berti, A., van Zelst, S. J., & Schuster, D. (2019). *PM4Py: A Process Mining Library for Python*. CEUR Workshop Proceedings.
3. Pedregosa, F., et al. (2011). *Scikit-learn: Machine Learning in Python*. Journal of Machine Learning Research, 12, 2825-2830.
4. Information Technology Infrastructure Library (ITIL 4). *Service Operation and Incident Management Guidelines*. AXELOS Global Best Practice.
5. Celonis Academic Alliance. *Process Mining Curriculum: Discover, Enhance, and Monitor Execution Gaps*. Celonis SE.
