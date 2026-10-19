"""
Sky Survey Schema Validator
===========================

Ensures required columns exist and have correct dtypes.
"""


def validate_sky_survey_schema(df):
    required = {
        "RAdeg": float,
        "DEdeg": float,
        "redshift": float,
    }

    for col, dtype in required.items():
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        if not df[col].dtype.kind in ("f", "i"):
            raise TypeError(f"Column {col} must be numeric")

    return True
