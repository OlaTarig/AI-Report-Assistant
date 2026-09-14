import pandas as pd

SAMPLE_ROWS = 5


def extract(path) -> dict:
    sheets = pd.read_excel(path, sheet_name=None)

    sheet_summaries = []
    text_parts = []

    for name, df in sheets.items():
        columns = list(df.columns.astype(str))
        row_count = len(df)
        # Cast to str before serializing — pandas cell values (Timestamps,
        # NaN, numpy types) aren't JSON-safe as-is.
        sample = df.head(SAMPLE_ROWS).astype(str).to_dict(orient="records")

        sheet_summaries.append(
            {"name": name, "columns": columns, "row_count": row_count, "sample_rows": sample}
        )
        text_parts.append(
            f"Sheet '{name}': {row_count} rows. Columns: {', '.join(columns)}\n"
            f"Sample:\n{df.head(SAMPLE_ROWS).to_string(index=False)}"
        )

    return {
        "sheets": sheet_summaries,
        "text_summary": "\n\n".join(text_parts),
    }
