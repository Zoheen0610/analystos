import pandas as pd
import numpy as np
from scipy import stats

def profile_dataset(df: pd.DataFrame) -> dict:
    profile = {
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": list(df.columns),
        "missing": {},
        "dtypes": {},
        "skewness": {},
        "outliers": {},
        "correlations": [],
        "duplicates": int(df.duplicated().sum())
    }

    for col in df.columns:
        # dtypes
        profile["dtypes"][col] = str(df[col].dtype)

        # missing values
        missing_count = int(df[col].isnull().sum())
        if missing_count > 0:
            profile["missing"][col] = {
                "count": missing_count,
                "percent": round((missing_count / len(df)) * 100, 2)
            }

        # numeric column analysis
        if pd.api.types.is_numeric_dtype(df[col]):
            skew = float(df[col].skew())
            if abs(skew) > 1:
                profile["skewness"][col] = round(skew, 3)

            # outliers using IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_count = int(((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)).sum())
            if outlier_count > 0:
                profile["outliers"][col] = outlier_count

    # top correlations among numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] > 1:
        corr_matrix = numeric_df.corr().abs()
        pairs = []
        cols = corr_matrix.columns
        for i in range(len(cols)):
            for j in range(i+1, len(cols)):
                val = corr_matrix.iloc[i, j]
                if val > 0.6 and not np.isnan(val):
                    pairs.append({
                        "col1": cols[i],
                        "col2": cols[j],
                        "correlation": round(float(val), 3)
                    })
        pairs.sort(key=lambda x: x["correlation"], reverse=True)
        profile["correlations"] = pairs[:10]  # top 10 only

    return profile