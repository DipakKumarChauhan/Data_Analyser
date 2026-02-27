## Tailor-Talk Agent – CSV Data Analyzer

An LLM-powered data analysis assistant for tabular (CSV) datasets.  
It lets non-technical users explore a dataset in natural language (e.g. “What percentage of passengers survived?” or “Show age distribution as histogram”) while the backend translates those questions into **deterministic analytics and visualizations**.

---

## 1. Project Overview

- **Goal**: Provide a conversational interface to analyze CSV datasets safely and reproducibly.
- **Key Idea**:  
  Natural-language questions → LLM converts them into a **structured intent JSON** → a deterministic **orchestrator** runs analytics/plots on a pandas DataFrame and returns:
  - Human-readable text
  - Optional Plotly chart (as JSON)
  - Optional structured numeric/tabular data

- **Default Dataset**: Titanic dataset (loaded on backend startup).
- **Custom Datasets**: Users can upload **any CSV** via the Streamlit UI; each upload gets its own **session** and is analyzed in the same way as the default dataset.

---

## 2. Architecture

### High-Level Components

- **Backend** (`backend/`):
  - FastAPI app (`app/main.py`, `app/api/routes.py`)
  - LLM + LangChain tool-based agent (`app/agent/*`)
  - Dataset/session management (`app/core/*`)
  - Analytics/aggregation/visualization tools (`app/tools/*`)
  - Data preprocessing utilities (`app/utils/*`)

- **Frontend** (`frontend/`):
  - Streamlit application (`frontend/streamlit_app.py`)
  - Provides a chat-style UI, dataset upload, session selection, and chart rendering.

### Data Flow

1. User opens Streamlit UI, chooses:
   - Default **Titanic** dataset, or
   - Uploads their own CSV (creating a new session with a unique `session_id`).
2. User types a natural-language question.
3. Frontend calls `POST /chat` with:
   - `query`: the user question
   - `session_id`: current dataset session
4. Backend `run_agent`:
   - Sends a **system prompt** + user message to the LLM with the `dataset_analyst` tool bound.
   - LLM decides whether to call the `dataset_analyst` tool.
5. `dataset_analyst` tool:
   - Fetches dataset schema for `session_id`.
   - Calls `parse_intent(question, schema)` to get structured intent.
   - Calls `orchestrator.execute(session_id, intent)` for deterministic execution.
6. Orchestrator:
   - Runs appropriate analytics/aggregation/visualization on the DataFrame.
   - Returns text + optional chart JSON + data.
7. Agent sends a **compact summary** of tool results back to the LLM (to keep token usage low).
8. Final LLM answer + tool outputs are returned to the frontend.
9. Streamlit displays:
   - Assistant text answer
   - Plotly chart (if any)
   - Optional raw JSON data in an expander.

---

## 3. Backend Details

### 3.1 Entry Point

- **`backend/app/main.py`**
  - Creates FastAPI app with `APP_NAME` from config.
  - On startup:
    - Loads Titanic dataset via `DatasetManager.load_titanic_dataset()`.
    - Registers it as the default session (`session_id = "titanic_default"`).
  - Includes the API router from `app/api/routes.py`.

### 3.2 Configuration

- **`backend/app/config.py`**

Environment is managed with `pydantic_settings.BaseSettings`:

- `APP_NAME`: Application name (shown in FastAPI & optionally in frontend titles).
- `DATA_DIR`: Data directory (defaults to `backend/app/data`).
- `TITANIC_DATASET`: Filename of the default dataset (default: `titanic.csv`).
- `GROQ_API_KEY`: API key for Groq (required).
- `GEMINI_API_KEY`: API key for Google Gemini (optional; Gemini client is currently commented).

**.env example:**

```env
APP_NAME=Tailor-Talk CSV Data Analyzer
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### 3.3 LLM Client

- **`backend/app/agent/llm_client.py`**

Configured to use **Groq**:

- Model: `llama-3.1-8b-instant`
- Temperature: `0` (deterministic)
- Optional Gemini client is wired but commented out.

### 3.4 Agent & Tools

#### `agent_executor.py`

- Binds LLM to `LANGCHAIN_TOOLS` (which includes `dataset_analyst`).
- Uses a **system prompt** that:
  - Restricts the assistant to dataset analysis.
  - Forbids using raw libraries like pandas/matplotlib directly.
  - Requires that all data questions go through the `dataset_analyst` tool.
  - Instructs: if a question is **not about the dataset** or its columns, **do not** call tools; instead reply with a short message explaining that only dataset analysis is supported.
- Implements a **tool-calling loop** with:
  - A **maximum number of tool iterations** to prevent infinite tool loops.
  - After each tool result, it appends a **small JSON summary** (text_response, chart flag, small data preview) to messages instead of the full chart/data JSON, to stay within Groq’s token limits.
- Enforces the current `session_id` on every tool call:
  - Ensures analysis always uses the dataset selected in the frontend (Titanic vs uploaded CSV).

#### `langchain_tools.py`

- Defines the `dataset_analyst` tool (as a `StructuredTool`):
  - `DatasetQueryInput`:
    - `query: str`
    - `session_id: Optional[str] = "titanic_default"`
  - `dataset_analysis_tool(query, session_id)`:
    1. Retrieves `DatasetManager` for the session.
    2. Gets the dataset schema.
    3. Calls `parse_intent(question, schema)` to get structured intent.
    4. Calls `orchestrator.execute(session_id, intent)`.
    5. Returns a JSON string with:
       - `text_response`
       - `chart` (Plotly `to_json()` string or `None`)
       - `data` (numeric/statistical results, or records for groupby).

- `LANGCHAIN_TOOLS = [dataset_analyst]`

#### `intent_parser.py`

- Uses `ChatPromptTemplate` to guide the LLM to output **strict JSON only**:

  - Allowed `intent` values: `analytics`, `aggregation`, `visualization`.
  - Allowed `operation` values (for analytics): `mean`, `percentage`, `count`.
  - Allowed charts: `histogram`, `bar_chart`, `pie_chart`, `area_chart`, `scatter`, `3d_scatter`.

- Prompt includes **detailed guidelines** for:
  - **Visualization** questions:
    - “Show X distribution as histogram/pie/area chart/…” → `intent: visualization`, `chart_type: ...`, `columns: [X]`.
  - **Percentage** questions:
    - “What percentage of people survived?” → `columns: ["survived"]`, `value: "1"`.
    - “What percentage of passengers were male?” → `columns: ["sex"]`, `value: "male"`.
    - Missing value questions (“what percentage of values are missing/NaN/null?”) → `value: "missing"`.
  - **Missing-value count** questions:
    - “How many missing values in COLUMN?” → `operation: "count"`, `value: "missing"`.
    - “How many non-missing/not null in COLUMN?” → `value: "non-missing"`.

- The parser:
  - Receives `schema` (with column names).
  - Builds a column list string and injects into the prompt.
  - Calls the LLM and **strictly parses** the response as JSON (stripping code fences if present).
  - Raises a clear error if the LLM returns invalid JSON.

### 3.5 Dataset & Session Management

#### `dataset_manager.py`

- Holds:
  - `raw_df`: original DataFrame.
  - `analysis_df`: preprocessed DataFrame (normalized columns, standardized missing values, coerced types).
  - `schema`: metadata:

    ```json
    {
      "columns": [{ "name": ..., "dtype": ... }, ...],
      "numeric_columns": [...],
      "categorical_columns": [...],
      "missing_values": { "<col>": <count>, ... }
    }
    ```

- Default Titanic dataset is loaded on startup.
- `get_dataframe()` returns the analysis DataFrame.
- `get_schema()` returns the schema.

#### `session_manager.py`

- Manages **multiple datasets** via sessions:
  - `initialize_default_session(base_dataset_manager)` → registers the Titanic dataset as `"titanic_default"`.
  - `create_session_from_dataframe(df)`:
    - Creates a new `DatasetManager` from the uploaded DataFrame.
    - Runs `preprocess_data` and `_generate_schema`.
    - Stores it under a generated UUID `session_id`.
  - `get_dataset_manager(session_id)` → returns the `DatasetManager` or raises a clear `ValueError` if the session does not exist.
  - `list_sessions()` → returns all active session IDs (useful for debugging).

### 3.6 Analytics, Aggregation & Visualization

#### Tools (`app/tools`)

- **`analytics_tool.py`**:
  - `calculate_mean(df, column)`:
    - Ensures column exists and is numeric.
  - `calculate_percentage(df, column, value)`:
    - Handles dtype-aware coercion of `value`.
    - Computes `% of rows where df[column] == value`.
  - `value_counts(df, column)`:
    - Returns `df[column].value_counts().to_dict()`.

- **`aggregation_tool.py`**:
  - `groupby_count(df, group_col)`
  - `groupby_mean(df, group_col, value_col)`

- **`visualization_tool.py`**:
  - Uses Plotly Express to build figures:
    - `create_histogram(df, column)`
    - `create_bar_chart(df, column)` (for categorical counts)
    - `create_pie_chart(df, column)` (with guards for too many categories & numeric constraints)
    - `create_area_chart(df, column)`
    - `create_scatter(df, x, y)`
    - `create_3d_scatter(df, x, y, z)`

#### Orchestrator (`orchestrator.py`)

- **`execute(session_id, intent)`**:
  - Retrieves `df` and schema for the provided `session_id`.
  - Routes by `intent["intent"]`:
    - `analytics` → `_handle_analytics(df, schema, intent)`
    - `aggregation` → `_handle_aggregation(df, intent)`
    - `visualization` → `_handle_visualization(df, intent)`

- **`_handle_analytics`**:
  - Validates and corrects columns via `tool_validator`.
  - Supports:
    - `mean` → `calculate_mean`.
    - `percentage` → handles:
      - Equality-based percentages.
      - Special phrases like “not 0”, “non-missing”, “missing”.
      - Infers sensible defaults when `value` is empty (e.g., survived positive class).
      - Uses schema’s `missing_values` when appropriate.
    - `count` → supports:
      - Missing/non-missing counts via schema.
      - Default value counts.
      - Auto-generation of a bar chart for count distributions (for some queries).
  - Always returns:
    - `text_response`: natural language summary.
    - `chart`: Plotly JSON or `None`.
    - `data`: underlying numeric data (e.g., dict for counts, float for mean/percentage).

- **`_handle_aggregation`**:
  - `mean` and `count` groupby operations.
  - Returns a list of records for the grouped results.

- **`_handle_visualization`**:
  - Validates chart type vs column (e.g., disallows pie on high-cardinality numeric columns).
  - Chooses appropriate Plotly builder.
  - Returns the chart as `fig.to_json()`.

### 3.7 Validation (`tool_validator.py`)

- **Column validation**:
  - Normalizes requested column names to lowercase.
  - First checks exact match, then uses **RapidFuzz** to fuzzily match to existing columns.
  - Raises a clear error if no reasonable match is found.

- **Chart validation**:
  - Ensures:
    - Histogram on non-numeric columns is redirected to a bar chart.
    - Pie charts on high-cardinality numeric or categorical columns are downgraded to histogram/bar.
    - Area charts require numeric columns; otherwise downgraded to bar chart.

- **Analytics validation**:
  - Ensures at least one column is provided.
  - Enforces numeric type only for `mean` operations.

---

## 4. API Reference (Backend)

All endpoints are under the FastAPI app (typically served via Uvicorn at `http://127.0.0.1:8000`).

- **GET `/health`**
  - Returns basic health check.

- **GET `/dataset-schema`**
  - Returns schema for the default Titanic dataset.

- **GET `/dataset-schema/{session_id}`**
  - Returns schema for a specific uploaded dataset session.
  - Errors with 500 if the session does not exist (internally a `ValueError` is raised).

- **POST `/upload-dataset`**
  - Body: `file` (CSV upload).
  - Creates a new session and returns:
    - `session_id`
    - `schema` for the uploaded dataset.

- **POST `/chat`**
  - Body (`ChatRequest`):
    - `query: str`
    - `session_id: str = "titanic_default"`
  - Returns:
    - `success: bool`
    - `response: str` (assistant text)
    - `chart: str | null` (Plotly figure JSON)
    - `data: any` (numeric/tabular data used in the answer)

---

## 5. Frontend (Streamlit)

- **File**: `frontend/streamlit_app.py`
- **Backend URL**: `BACKEND_URL = "http://127.0.0.1:8000"`

### Features

- Left sidebar:
  - Dataset mode:
    - “Titanic Dataset”
    - “Upload CSV”
  - CSV uploader:
    - On upload, calls `/upload-dataset`, stores returned `session_id` in `st.session_state`, and displays the schema.
  - Displays current session ID.
  - “Clear Chat History” button.

- Main area:
  - Header + caption.
  - Chat history:
    - Renders user and assistant messages using `st.chat_message`.
    - Renders Plotly charts with unique keys to avoid duplicate ID errors when re-rendering chat history.
  - Chat input:
    - Sends `query` and current `session_id` to `/chat`.
    - Shows spinner while waiting.
    - Displays assistant response, chart, and optional “View Raw Data” expander.

---

## 6. Setup & Usage

### 6.1 Prerequisites

- Python 3.10+
- Groq API key.

### 6.2 Backend Setup

From `backend/`:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` with `APP_NAME` and `GROQ_API_KEY`.

Run the backend:

```bash
uvicorn app.main:app --reload
```

### 6.3 Frontend Setup

From `frontend/`:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

---

## 7. Known Limitations & Notes

- **Provider Limits**:
  - Groq enforces **tokens-per-minute (TPM) limits**. Very long conversations or large tool outputs can hit a `413` / `rate_limit_exceeded` error.
  - The agent mitigates this by:
    - Summarizing tool outputs before sending them back to the LLM.
    - Imposing a cap on tool iterations.
  - Still, very long chat histories can grow the prompt; restarting the backend or clearing chat can help.

- **Off-topic Questions**:
  - The agent is explicitly instructed:
    - If a question is not about the dataset or its columns, **do not** call tools.
    - Respond with a short text explanation that it only analyzes datasets.

- **Filters / Row-level Conditions**:
  - As currently implemented, intents focus primarily on:
    - Single-column analytics (`mean`, `percentage`, `count`).
    - Grouped aggregations via `group_by`.
  - More complex row-level filters (e.g. “males who survived”) require:
    - The LLM to reliably emit filter conditions.
    - The orchestrator to apply those filters before analytics.

- **Schema as Source of Truth**:
  - Missing-value statistics are precomputed in the schema and, where possible, **reused** by analytics instead of being recomputed from the DataFrame.
  - This ensures consistent missing counts across different queries.

---

## 8. Development & Testing

- Manual test scripts are provided under `backend/app/test/` (e.g., for validator, intent parser, orchestrator).
- Recommended dev workflow:
  - Start the backend with `--reload`.
  - Start the Streamlit frontend.
  - Use the Titanic dataset for quick iteration.
  - Once stable, test with a variety of custom CSVs (different schemas, column names, missing patterns).
