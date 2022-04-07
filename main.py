from datetime import datetime, timedelta
import pathlib
from functools import partial
from statistics import mean
from typing import List, Tuple

import pandas as pd
from dateutil.parser import parse as date_parse
from thefuzz import fuzz

thisdir = pathlib.Path(__file__).resolve().parent

def score(clauses: List[List[str]], topics: str) -> float:
    return min( # max match across clauses - ALL clauses should match
        max( # max across topics and queries - any query can match any topic
            fuzz.partial_ratio(
                query.strip().lower(), 
                topic.strip().lower()
            )
            for topic in topics.split(" // ")
            for query in clause
        )
        for clause in clauses
    )

def load_data() -> pd.DataFrame:
    df = pd.read_csv(thisdir.joinpath("data.csv"))
    df.loc[:, "Last Deadline"] = df["Last Deadline"].apply(date_parse)
    df["CORE Rank"] = pd.Categorical(df["CORE Rank"], ["A*", "A", "B", "C"])
    return df

def query_data(df: pd.DataFrame, query: List[List[str]]) -> pd.DataFrame:
    df.loc[:, "Query Score"] = df["Topics"].apply(partial(score, query))
    return df

SORT_COLS = ["CORE Rank", "ERA Rank", "Qualis Rank", "h5-index"]
DESCENDING_COLS = {"Query Score"}
def sort_data(df: pd.DataFrame, 
              cols: List[str] = SORT_COLS) -> pd.DataFrame:
    return df.sort_values(
        by=cols,
        ascending=[col not in DESCENDING_COLS for col in cols]
    )

def to_report(df: pd.DataFrame) -> str:
    columns = ["Conference", "h5-index", "CORE Rank", "ERA Rank", "Qualis Rank", "Last Deadline", "Name", "Query Score"]
    columns = [col for col in df.columns if col in columns]
    df.loc[:, "Last Deadline"] = df["Last Deadline"].dt.strftime("%b %d")
    return df[columns].to_string(index=None)


# API
def do_query(query: List[List[str]]) -> None:
    df = load_data()
    if query:
        df = sort_data(
            query_data(df, query),
            cols=["Query Score", *SORT_COLS]
        )
    else:
        df = sort_data(df)

    print(to_report(df))

def do_upcoming_deadlines(query: List[List[str]],
                          day_pad: int = 0) -> None:
    df = load_data()
    df = df[df["Last Deadline"] - timedelta(days=day_pad) >= datetime.today()]
    if query:
        df = sort_data(
            query_data(df, query),
            cols=["Query Score", "Last Deadline", *SORT_COLS]
        )
    else:
        df = sort_data(df, ["Last Deadline", *SORT_COLS])

    print(to_report(df))

def main():
    query = [
        ["mobile"],
        ["agent", "robot"]
    ]

    # do_query(query)
    do_upcoming_deadlines(query)


if __name__ == "__main__":
    main()
