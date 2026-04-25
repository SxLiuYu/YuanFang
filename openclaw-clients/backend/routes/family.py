from fastapi import APIRouter, Request
import logging
from services.family_service import (
    family_service, FamilyGroupCreate, FamilyGroupUpdate,
    FamilyMemberAdd, LocationShare, SharedScheduleCreate
)
from shared import success_response, error_response

router = APIRouter(prefix="/api/v1/family", tags=["family"])

@router.post("/groups")
async def create_family_group(request: FamilyGroupCreate):
    try:
        result = await family_service.create_group(request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Create family group error: {e}")
        return error_response(str(e))

@router.get("/groups/{group_id}")
async def get_family_group(group_id: str):
    try:
        result = await family_service.get_group(group_id)
        if result:
            return success_response(result)
        return error_response("群组不存在", 404)
    except Exception as e:
        logging.error(f"Get family group error: {e}")
        return error_response(str(e))

@router.put("/groups/{group_id}")
async def update_family_group(group_id: str, request: FamilyGroupUpdate):
    try:
        result = await family_service.update_group(group_id, request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Update family group error: {e}")
        return error_response(str(e))

@router.delete("/groups/{group_id}")
async def delete_family_group(group_id: str, owner_id: str):
    try:
        result = await family_service.delete_group(group_id, owner_id)
        return success_response(result)
    except Exception as e:
        logging.error(f"Delete family group error: {e}")
        return error_response(str(e))

@router.get("/user/{user_id}/groups")
async def get_user_groups(user_id: str):
    try:
        result = await family_service.get_user_groups(user_id)
        return success_response(result)
    except Exception as e:
        logging.error(f"Get user groups error: {e}")
        return error_response(str(e))

@router.post("/groups/{group_id}/members")
async def add_family_member(group_id: str, request: FamilyMemberAdd):
    try:
        request.group_id = group_id
        result = await family_service.add_member(request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Add family member error: {e}")
        return error_response(str(e))

@router.post("/join")
async def join_family_group(invite_code: str, user_id: str, name: str):
    try:
        result = await family_service.join_group(invite_code, user_id, name)
        return success_response(result)
    except Exception as e:
        logging.error(f"Join family group error: {e}")
        return error_response(str(e))

@router.delete("/groups/{group_id}/members/{user_id}")
async def remove_family_member(group_id: str, user_id: str, operator_id: str):
    try:
        result = await family_service.remove_member(group_id, user_id, operator_id)
        return success_response(result)
    except Exception as e:
        logging.error(f"Remove family member error: {e}")
        return error_response(str(e))

@router.post("/location/share")
async def share_family_location(request: LocationShare):
    try:
        result = await family_service.share_location(request.user_id, request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Share location error: {e}")
        return error_response(str(e))

@router.get("/groups/{group_id}/location/members")
async def get_member_locations(group_id: str):
    try:
        result = await family_service.get_member_locations(group_id)
        return success_response(result)
    except Exception as e:
        logging.error(f"Get member locations error: {e}")
        return error_response(str(e))

@router.post("/calendar/shared")
async def create_shared_calendar(request: SharedScheduleCreate):
    try:
        result = await family_service.create_shared_schedule(request)
        return success_response(result)
    except Exception as e:
        logging.error(f"Create shared schedule error: {e}")
        return error_response(str(e))

@router.get("/groups/{group_id}/calendar/shared")
async def get_shared_calendars(group_id: str, start_date: str = None, end_date: str = None):
    try:
        result = await family_service.get_group_schedules(group_id, start_date, end_date)
        return success_response(result)
    except Exception as e:
        logging.error(f"Get shared calendars error: {e}")
        return error_response(str(e))