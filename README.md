# Personal Expense Tracker (Streamlit)

A small Python + Streamlit project to track daily expenses, view summaries, and download filtered data.

## Features
- Add expenses from a sidebar form
- Filter by date range and category
- View KPI cards for total spend, average spend, largest expense, and transaction count
- See category-wise and daily charts
- Download filtered transactions as CSV
- Delete a selected transaction or clear all data

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push these files to a GitHub repository.
2. Go to Streamlit Community Cloud.
3. Choose **New app** and select the repo.
4. Set the main file path to `app.py`.
5. Deploy.

## File structure

- `app.py`
- `requirements.txt`
- `README.md`
