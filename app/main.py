"""FastAPI application that exposes Steam game recommendations."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECS_PATH = PROJECT_ROOT / "data" / "reporting" / "recommendations_top5.csv"

_RECS_DF: pd.DataFrame = pd.DataFrame(
    columns=["user_id", "rank", "game_title", "score"]
)


def _load_recommendations(path: Path) -> pd.DataFrame:
    """Load precomputed recommendations from disk."""
    if not path.exists():
        logger.error("Recommendations file missing: %s", path)
        return pd.DataFrame(columns=["user_id", "rank", "game_title", "score"])

    df = pd.read_csv(path)
    df["user_id"] = df["user_id"].astype(int)
    logger.info(
        "Loaded recommendations: %d rows, %d unique users.",
        len(df),
        df["user_id"].nunique(),
    )
    return df


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Load recommendations once during application startup."""
    global _RECS_DF  # pylint: disable=global-statement
    _RECS_DF = _load_recommendations(RECS_PATH)
    yield


app = FastAPI(title="Steam Game Recommender API", version="1.0", lifespan=lifespan)


class Recommendation(BaseModel):
    """A single recommended game returned by the API."""

    rank: int
    game_title: str
    score: float


class RecommendationsResponse(BaseModel):
    """Response payload for the per-user recommendations endpoint."""

    user_id: int
    n_recommendations: int
    recommendations: list[Recommendation]


class UsersResponse(BaseModel):
    """Response payload for the list-of-users helper endpoint."""

    available_user_ids: list[int]
    total_unique_users: int


@app.get("/", summary="Health check")
def home() -> dict[str, str]:
    """Return a simple status message used as a health probe."""
    return {"message": "Steam Recommender API dziala poprawnie"}


@app.get("/users", response_model=UsersResponse, summary="List sample user IDs")
def list_users(limit: int = 20) -> UsersResponse:
    """Return up to ``limit`` user IDs that have recommendations available."""
    if _RECS_DF.empty:
        raise HTTPException(status_code=503, detail="Recommendations are not loaded.")

    ids = _RECS_DF["user_id"].drop_duplicates().head(limit).tolist()
    return UsersResponse(
        available_user_ids=ids,
        total_unique_users=int(_RECS_DF["user_id"].nunique()),
    )


@app.get(
    "/users/{user_id}/recommendations",
    response_model=RecommendationsResponse,
    summary="Top-K recommendations for a user",
)
def get_recommendations(user_id: int) -> RecommendationsResponse:
    """Return precomputed Top-K recommendations for the given Steam ``user_id``."""
    if _RECS_DF.empty:
        raise HTTPException(status_code=503, detail="Recommendations are not loaded.")

    user_recs = _RECS_DF[_RECS_DF["user_id"] == user_id].sort_values("rank")
    if user_recs.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No recommendations found for user_id={user_id}.",
        )

    items = [
        Recommendation(
            rank=int(row["rank"]),
            game_title=str(row["game_title"]),
            score=float(row["score"]),
        )
        for _, row in user_recs.iterrows()
    ]
    return RecommendationsResponse(
        user_id=user_id,
        n_recommendations=len(items),
        recommendations=items,
    )
