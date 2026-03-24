# routers/insights_router.py
from fastapi import APIRouter, HTTPException
from repositories.insights_repository import predict_daily_spending, analyze_spending_trends
from charts.insights_charts import plot_spending_trend, plot_category_distribution

router = APIRouter()

@router.get("/daily_prediction")
def daily_prediction(user_id: float):
    try:
        return predict_daily_spending(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in prediction: {str(e)}")


@router.get("/ai_trends")
def ai_trends(user_id: float):
    try:
        return analyze_spending_trends(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in trend analysis: {str(e)}")


# 🧩 NEW Visualization Endpoints

@router.get("/spending_chart")
def spending_chart(user_id: float):
    """Generate spending trend line chart (returns base64 image)."""
    try:
        return plot_spending_trend(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")


@router.get("/category_chart")
def category_chart(user_id: float):
    """Generate category-wise pie chart (returns base64 image)."""
    try:
        return plot_category_distribution(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")
    

@router.get("/daily_spending/{user_id}")
def get_daily_spending(user_id: float):
    try:
        return predict_daily_spending(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {e}")
