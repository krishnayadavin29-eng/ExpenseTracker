import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

DATA_FILE = Path(os.environ.get("DATA_FILE", "/tmp/expenses.csv"))
COLUMNS = ["date", "category", "description", "amount", "payment_mode"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Personal Expense Tracker</title>
    <style>
      :root {
        --bg: #f3f4f6;
        --panel: #ffffff;
        --primary: #2563eb;
        --text: #111827;
        --muted: #6b7280;
        --danger: #dc2626;
        --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      .container {
        max-width: 1100px;
        margin: 32px auto;
        padding: 0 16px 48px;
      }
      h1 { margin: 0 0 8px; }
      .subtitle {
        color: var(--muted);
        margin: 0 0 24px;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin: 24px 0;
      }
      .card {
        background: var(--panel);
        padding: 18px;
        border-radius: 16px;
        box-shadow: var(--shadow);
      }
      .card-label { color: var(--muted); font-size: 14px; margin-bottom: 8px; }
      .card-value { font-size: 26px; font-weight: 700; }
      .layout {
        display: grid;
        grid-template-columns: 360px 1fr;
        gap: 24px;
      }
      .panel {
        background: var(--panel);
        border-radius: 16px;
        box-shadow: var(--shadow);
        padding: 20px;
      }
      form {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      label {
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 14px;
      }
      input, select, button {
        border-radius: 10px;
        border: 1px solid #d1d5db;
        padding: 10px 12px;
        font-size: 15px;
      }
      input:focus, select:focus { outline: 2px solid rgba(37, 99, 235, 0.2); border-color: var(--primary); }
      button {
        background: var(--primary);
        border: none;
        color: white;
        cursor: pointer;
        font-weight: 600;
      }
      .secondary { background: #e5e7eb; color: var(--text); }
      .danger { background: var(--danger); }
      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 18px;
      }
      th, td {
        border-bottom: 1px solid #e5e7eb;
        padding: 10px 8px;
        text-align: left;
        font-size: 14px;
      }
      th { color: var(--muted); font-weight: 600; }
      .message {
        padding: 12px 14px;
        border-radius: 10px;
        margin-bottom: 16px;
        background: #ecfdf5;
        color: #166534;
      }
      .error {
        background: #fef2f2;
        color: #991b1b;
      }
      .empty {
        padding: 30px 0;
        text-align: center;
        color: var(--muted);
      }
      @media (max-width: 840px) { .layout { grid-template-columns: 1fr; } }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>💸 Personal Expense Tracker</h1>
      <p class="subtitle">Add, review, and manage your spending.</p>

      {% if message %}
        <div class="message {% if message_type == 'error' %}error{% endif %}">{{ message }}</div>
      {% endif %}

      <div class="grid">
        <div class="card"><div class="card-label">Total spent</div><div class="card-value">{{ total_spent }}</div></div>
        <div class="card"><div class="card-label">Average expense</div><div class="card-value">{{ avg_spend }}</div></div>
        <div class="card"><div class="card-label">Largest expense</div><div class="card-value">{{ largest_expense }}</div></div>
        <div class="card"><div class="card-label">Transactions</div><div class="card-value">{{ transactions }}</div></div>
      </div>

      <div class="layout">
        <aside class="panel">
          <h2>Add new expense</h2>
          <form method="POST" action="{{ url_for('add_expense') }}">
            <label>
              Date
              <input type="date" name="date" value="{{ today }}" required />
            </label>
            <label>
              Category
              <select name="category">
                <option>Food</option>
                <option>Travel</option>
                <option>Bills</option>
                <option>Shopping</option>
                <option>Education</option>
                <option>Health</option>
                <option>Entertainment</option>
                <option>Other</option>
              </select>
            </label>
            <label>
              Description
              <input type="text" name="description" placeholder="e.g. Lunch with friends" />
            </label>
            <label>
              Amount (₹)
              <input type="number" name="amount" min="0.01" step="0.01" required />
            </label>
            <label>
              Payment mode
              <select name="payment_mode">
                <option>Cash</option>
                <option>UPI</option>
                <option>Card</option>
                <option>Net Banking</option>
                <option>Other</option>
              </select>
            </label>
            <button type="submit">Save expense</button>
          </form>

          <div style="margin-top: 20px;">
            <form method="POST" action="{{ url_for('clear_all') }}">
              <button type="submit" class="secondary">Clear all data</button>
            </form>
          </div>
        </aside>

        <main class="panel">
          <h2>Transactions</h2>
          {% if expenses %}
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Category</th>
                  <th>Description</th>
                  <th>Payment</th>
                  <th>Amount</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {% for row in expenses %}
                  <tr>
                    <td>{{ row.date }}</td>
                    <td>{{ row.category }}</td>
                    <td>{{ row.description }}</td>
                    <td>{{ row.payment_mode }}</td>
                    <td>{{ row.amount }}</td>
                    <td>
                      <form method="POST" action="{{ url_for('delete_expense', index=row.index) }}">
                        <button type="submit" class="danger">Delete</button>
                      </form>
                    </td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          {% else %}
            <div class="empty">No records added yet.</div>
          {% endif %}
        </main>
      </div>
    </div>
  </body>
</html>
"""


def initialize_storage() -> None:
    if not DATA_FILE.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)


def load_data() -> pd.DataFrame:
    initialize_storage()
    try:
        df = pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNS].copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["category"] = df["category"].fillna("Other").astype(str)
    df["description"] = df["description"].fillna("").astype(str)
    df["payment_mode"] = df["payment_mode"].fillna("Cash").astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "amount"]).copy()

    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    df["amount"] = df["amount"].astype(float)
    df["date"] = df["date"].astype("datetime64[ns]")
    return df.sort_values("date", ascending=False).reset_index(drop=True)


def save_data(df: pd.DataFrame) -> None:
    out = df.copy()
    if pd.api.types.is_datetime64_any_dtype(out["date"]):
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_FILE, index=False)


def format_currency(value: float) -> str:
    return f"₹{value:,.2f}"


@app.route("/", methods=["GET"])
def home():
    df = load_data()
    total_spent = format_currency(df["amount"].sum() if not df.empty else 0.0)
    avg_spend = format_currency(df["amount"].mean() if not df.empty else 0.0)
    largest_expense = format_currency(df["amount"].max() if not df.empty else 0.0)
    transaction_count = len(df)

    expense_rows = []
    for idx, row in df.reset_index(drop=True).iterrows():
        expense_rows.append({
            "index": idx,
            "date": row["date"].strftime("%Y-%m-%d"),
            "category": row["category"],
            "description": row["description"],
            "payment_mode": row["payment_mode"],
            "amount": format_currency(float(row["amount"])),
        })

    return render_template_string(
        HTML_TEMPLATE,
        total_spent=total_spent,
        avg_spend=avg_spend,
        largest_expense=largest_expense,
        transactions=transaction_count,
        today=datetime.utcnow().strftime("%Y-%m-%d"),
        expenses=expense_rows,
        message=None,
        message_type="info",
    )


@app.route("/add", methods=["POST"])
def add_expense():
    df = load_data()
    expense_date = request.form.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
    category = (request.form.get("category") or "Other").strip() or "Other"
    description = (request.form.get("description") or "").strip()
    amount = float(request.form.get("amount") or 0)
    payment_mode = (request.form.get("payment_mode") or "Cash").strip() or "Cash"

    if amount <= 0:
        return render_template_string(
            HTML_TEMPLATE,
            total_spent=format_currency(df["amount"].sum() if not df.empty else 0.0),
            avg_spend=format_currency(df["amount"].mean() if not df.empty else 0.0),
            largest_expense=format_currency(df["amount"].max() if not df.empty else 0.0),
            transactions=len(df),
            today=datetime.utcnow().strftime("%Y-%m-%d"),
            expenses=[{
                "index": idx,
                "date": row["date"].strftime("%Y-%m-%d"),
                "category": row["category"],
                "description": row["description"],
                "payment_mode": row["payment_mode"],
                "amount": format_currency(float(row["amount"])),
            } for idx, row in df.reset_index(drop=True).iterrows()],
            message="Amount must be greater than zero.",
            message_type="error",
        )

    new_row = pd.DataFrame([{
        "date": pd.Timestamp(expense_date),
        "category": category,
        "description": description,
        "amount": amount,
        "payment_mode": payment_mode,
    }])
    new_row["date"] = new_row["date"].astype("datetime64[ns]")
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    return redirect(url_for("home"))


@app.route("/delete/<int:index>", methods=["POST"])
def delete_expense(index: int):
    df = load_data()
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        save_data(df)
    return redirect(url_for("home"))


@app.route("/clear", methods=["POST"])
def clear_all():
    pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
