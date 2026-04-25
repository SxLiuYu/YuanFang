from fastapi import APIRouter
import logging
from typing import Optional
from services.shopping_service import shopping_service
from services.recipe_service import recipe_service
from shared import success_response, error_response, ShoppingItemRequest

router = APIRouter(tags=["shopping-recipe"])

# Shopping
@router.post("/api/v1/shopping/item/add")
async def shopping_item_add(request: ShoppingItemRequest):
    try:
        result = await shopping_service.add_item(
            name=request.name, quantity=request.quantity, category=request.category
        )
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/shopping/list")
async def shopping_list():
    try:
        result = await shopping_service.get_list()
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.put("/api/v1/shopping/item/check")
async def shopping_item_check(item_id: str):
    try:
        result = await shopping_service.check_item(item_id)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/shopping/inventory/query")
async def shopping_inventory_query(item_name: str):
    try:
        result = await shopping_service.query_inventory(item_name)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

# Recipe
@router.get("/api/v1/recipe/recommend")
async def recipe_recommend(ingredients: Optional[str] = None):
    try:
        result = await recipe_service.recommend(ingredients)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/recipe/search")
async def recipe_search(keyword: str):
    try:
        result = await recipe_service.search(keyword)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.get("/api/v1/recipe/detail")
async def recipe_detail(recipe_id: str):
    try:
        result = await recipe_service.get_detail(recipe_id)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/api/v1/recipe/timer/start")
async def recipe_timer_start(minutes: int, label: Optional[str] = None):
    try:
        result = await recipe_service.start_timer(minutes, label)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))