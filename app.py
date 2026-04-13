import os
from datetime import date, datetime

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

APP_TITLE = "Personal Expense Tracker"
DATA_FILE = "expenses.csv"
COLUMNS = ["date", "category", "description", "amount", "payment_mode"]

st.set_page_config(page_title=APP_TITLE, page_icon="💸", layout="wide")


def initialize_storage() -> None:
    """Create the CSV file with headers if it does not exist."""
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(DATA_FILE, index=False)


def load_data() -> pd.DataFrame:
    """Load expense data from CSV and normalize types."""
    initialize_storage()
    try:
        df = pd.read_csv(DATA_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    # Ensure expected columns exist even if the file was edited manually.
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    df["amount"] = df["amount"].astype(float)
    df["category"] = df["category"].fillna("Other").astype(str)
    df["description"] = df["description"].fillna("").astype(str)
    df["payment_mode"] = df["payment_mode"].fillna("Cash").astype(str)
    return df.sort_values("date", ascending=False).reset_index(drop=True)


def save_data(df: pd.DataFrame) -> None:
    """Save expense data to CSV."""
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_FILE, index=False)


def add_expense(expense_date: date, category: str, description: str, amount: float, payment_mode: str) -> None:
    df = load_data()
    new_row = pd.DataFrame(
        [{
            "date": pd.to_datetime(expense_date),
            "category": category.strip() or "Other",
            "description": description.strip(),
            "amount": float(amount),
            "payment_mode": payment_mode.strip() or "Cash",
        }]
    )
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    st.success("Expense saved successfully.")


def delete_row(index: int) -> None:
    df = load_data()
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        save_data(df)
        st.success("Expense deleted.")


def clear_all() -> None:
    df = pd.DataFrame(columns=COLUMNS)
    save_data(df)
    st.warning("All expenses cleared.")


def fmt_currency(value: float) -> str:
    return f"₹{value:,.2f}"


def render_kpis(df: pd.DataFrame) -> None:
    total_spent = df["amount"].sum() if not df.empty else 0.0
    avg_spend = df["amount"].mean() if not df.empty else 0.0
    largest = df["amount"].max() if not df.empty else 0.0
    txn_count = len(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total spent", fmt_currency(total_spent))
    c2.metric("Average expense", fmt_currency(avg_spend))
    c3.metric("Largest expense", fmt_currency(largest))
    c4.metric("Transactions", f"{txn_count}")


def render_charts(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Add some expenses to see charts.")
        return

    left, right = st.columns(2)

    category_totals = df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    with left:
        st.subheader("Spending by category")
        fig, ax = plt.subplots()
        ax.bar(category_totals["category"], category_totals["amount"])
        ax.set_xlabel("Category")
        ax.set_ylabel("Amount (₹)")
        ax.tick_params(axis="x", rotation=35)
        st.pyplot(fig, clear_figure=True)

    daily_totals = df.groupby(df["date"].dt.date, as_index=False)["amount"].sum()
    daily_totals = daily_totals.sort_values("date")
    with right:
        st.subheader("Daily spending")
        fig, ax = plt.subplots()
        ax.plot(daily_totals["date"], daily_totals["amount"], marker="o")
        ax.set_xlabel("Date")
        ax.set_ylabel("Amount (₹)")
        ax.tick_params(axis="x", rotation=35)
        st.pyplot(fig, clear_figure=True)


def main() -> None:
    initialize_storage()

    st.title("💸 Personal Expense Tracker")
    st.caption("A small Streamlit project to add, view, filter, and visualize your expenses.")

    with st.sidebar:
        st.header("Add new expense")
        with st.form("expense_form", clear_on_submit=True):
            expense_date = st.date_input("Date", value=date.today())
            category = st.selectbox(
                "Category",
                ["Food", "Travel", "Bills", "Shopping", "Education", "Health", "Entertainment", "Other"],
            )
            description = st.text_input("Description", placeholder="e.g. Lunch with friends")
            amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
            payment_mode = st.selectbox("Payment mode", ["Cash", "UPI", "Card", "Net Banking", "Other"])
            submitted = st.form_submit_button("Save expense")

            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    add_expense(expense_date, category, description, amount, payment_mode)

        st.divider()
        if st.button("Clear all data", type="secondary"):
            clear_all()

    df = load_data()

    render_kpis(df)

    st.subheader("Filters")
    f1, f2, f3 = st.columns(3)
    start_date = f1.date_input(
        "Start date",
        value=df["date"].min().date() if not df.empty else date.today(),
    )
    end_date = f2.date_input(
        "End date",
        value=df["date"].max().date() if not df.empty else date.today(),
    )
    categories = ["All"] + sorted(df["category"].dropna().unique().tolist()) if not df.empty else ["All"]
    selected_category = f3.selectbox("Category", categories)

    filtered = df.copy()
    if not df.empty:
        filtered = filtered[
            (filtered["date"].dt.date >= start_date)
            & (filtered["date"].dt.date <= end_date)
        ]
        if selected_category != "All":
            filtered = filtered[filtered["category"] == selected_category]

    render_charts(filtered)

    st.subheader("Transactions")
    if filtered.empty:
        st.info("No records match the selected filters.")
    else:
        display_df = filtered.copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        display_df["amount"] = display_df["amount"].map(lambda x: f"₹{x:,.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv_bytes = filtered.assign(date=filtered["date"].dt.strftime("%Y-%m-%d")).to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered data as CSV",
            data=csv_bytes,
            file_name="filtered_expenses.csv",
            mime="text/csv",
        )

        st.subheader("Delete a transaction")
        options = {
            f'{row.date.strftime("%Y-%m-%d")} | {row.category} | {row.description[:30]} | ₹{row.amount:,.2f}': idx
            for idx, row in filtered.reset_index(drop=True).iterrows()
        }
        choice = st.selectbox("Select transaction", list(options.keys()))
        if st.button("Delete selected transaction"):
            # Map back to the original dataframe index
            selected_row = filtered.reset_index()
            to_delete = int(selected_row.loc[selected_row.apply(
                lambda r: f'{r["date"].strftime("%Y-%m-%d")} | {r["category"]} | {str(r["description"])[:30]} | ₹{r["amount"]:,.2f}',
                axis=1
            ) == choice, "index"].iloc[0])
            delete_row(to_delete)


if __name__ == "__main__":
    main()
