"""
All API endpoints.
"""

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import plotly.express as px
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from src.db.mongo import init_db_connection
from src.routers import templates

router = APIRouter(
    prefix="/api",
    tags=["api"],
    responses={404: {"description": "Issue with endpoint"}},
)


@router.get("/live", include_in_schema=False)
async def api_live() -> JSONResponse:
    """
    Check if the api is up
    :return: a basic response
    """
    return JSONResponse({"message": "Hello, World"})


def dataframe_from_mongo_data(db_data):
    """
    Prepares the data retrieved from Mongo to be compliant with pd.DataFrame and JSONResponse
    :param db_data: data retrieved from Mongo
    :return: the prepared/cleaned dataframe
    """

    df = pd.DataFrame(db_data).drop(columns=["_id"])
    # drop_duplicates to cover potential overlaps from the GitHub events API
    clean_df = df.drop_duplicates().replace(to_replace=[np.nan], value=[""])
    return clean_df


@router.get("/pr_deltas_timeline")
async def pr_deltas_timeline(request: Request, repo_name: str, size: int = None):
    """
    Plots a diagram showing the time deltas between the last n PRs for that repo.
    Generates a unique html template for each call, based on repo name and timestamp
    :param repo_name: name of the repository to check
    :param size: how much PRs will be displayed (needs to be higher than 2 to generate to enough delta points)
    :return: a json response
    """

    # data
    db = init_db_connection()
    db_data = db.event.find({"repo_name": repo_name})
    df = dataframe_from_mongo_data(db_data).sort_values(by="created_at")

    if size is not None and size > 2:
        results_df = df.tail(size).reset_index()
    else:
        results_df = df.reset_index()

    dates = pd.to_datetime(results_df["created_at"]).rename("#PR")
    deltas = dates.diff().dt.total_seconds().drop(index=0)
    plot_df = pd.DataFrame(
        list(zip(deltas.index, deltas)), columns=["#PR", "delta (seconds)"]
    ).astype({"#PR": "int32"})

    # diagram
    fig = px.line(plot_df, x="#PR", y="delta (seconds)")
    fig.update_xaxes(nticks=plot_df.shape[0])  # shows only integers for that axe

    title_text = f"{repo_name} PR deltas timeline"
    if size is not None and size < 3:
        title_text += "<br><span style='font-size: .8rem;'>/!\\ the required size is too small (< 2)</span>"
    fig.update_layout(title_text=title_text)

    # html
    timestamp = datetime.now(timezone.utc).isoformat()
    normalized_repo_name = repo_name.replace("/", "_-_")
    html_template = f"pr_deltas_timeline_{normalized_repo_name}_{timestamp}.html"
    fig.write_html(f"templates/{html_template}")

    return templates.TemplateResponse(
        html_template,
        context={
            "request": request,
        },
    )


@router.get("/pr_average_delta")
async def pr_average_delta(repo_name: str):
    """
    Calculate the average time between pull requests for a given repository
    :param repo_name: name of the repository to check
    :return: a json response
    """

    db = init_db_connection()
    db_data = db.event.find({"repo_name": repo_name})
    results_df = dataframe_from_mongo_data(db_data)

    dates = pd.to_datetime(results_df["created_at"])
    deltas = dates.diff().dt.total_seconds()
    average_pr = round(deltas.drop(index=0).mean(), 3)  # rounded to millisecond floats

    return JSONResponse({"pr_average_time[seconds]": average_pr})


@router.get("/count_per_type")
async def count_per_type(offset: str):
    """
    Return the total number of events grouped by the event type for a given offset.
    The offset determines how much time we want to look back
    i.e. an offset of 10 means we count only the events which have been created in the last 10 minutes
    :param offset: offset in minutes
    :return: a json response
    """

    time_with_offset = (
        datetime.now(timezone.utc) - timedelta(minutes=int(offset))
    ).isoformat()
    offset_filter = {"created_at": {"$lte": f"{time_with_offset}"}}

    db = init_db_connection()
    db_data = db.event.find(offset_filter)
    results_df = dataframe_from_mongo_data(db_data)
    data = (
        results_df[["repo_name", "type"]]
        .rename(columns={"repo_name": "type_count"})
        .groupby(["type"])
        .count()
    )

    return JSONResponse(data.to_dict())

# TODO: endpoint focused on user activity
# potentially update the data flow and include that in mongo
"""
    "actor": {
                "id": 49699333,
                "login": "dependabot[bot]",
                "display_login": "dependabot",
                "gravatar_id": "",
                "url": "https://api.github.com/users/dependabot[bot]",
                "avatar_url": "https://avatars.githubusercontent.com/u/49699333?"
            },
"""
