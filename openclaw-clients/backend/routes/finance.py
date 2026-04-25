from fastapi import APIRouter
import logging
from typing import Optional
from services.finance_service import finance_service
from shared import success_response, error_response, TransactionRequest

router = APIRouter(prefix="/api/v1/finance", tags=["finance"])

@router.post("/transaction/add")
async def finance_transaction_add(request: TransactionRequest):
    try:
        result = await finance_service.add_transaction(
            amount=request.amount, category=request.category,
            type=request.type, description=request.description, date=request.date
        )
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/transaction/query")
async def finance_transaction_query(
    start_date: Optional[str] = None, end_date: Optional[str] = None,
    category: Optional[str] = None
):
    try:
        result = await finance_service.query_transactions(
            start_date=start_date, end_date=end_date, category=category
        )
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/report/daily")
async def finance_report_daily(date: Optional[str] = None):
    try:
        result = await finance_service.get_daily_report(date)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/report/monthly")
async def finance_report_monthly(month: Optional[str] = None):
    try:
        result = await finance_service.get_monthly_report(month)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/budget/status")
async def finance_budget_status():
    try:
        result = await finance_service.get_budget_status()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/asset/summary")
async def finance_asset_summary():
    try:
        result = await finance_service.get_asset_summary()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))