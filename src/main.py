"""
src/main.py
Здесь производятся основные запросы к базе данных.
При увеличении функциональности приложения перенести в файл query
"""
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models import Organization, OrganizationActivity, Building, Activity, PhoneNumber

app = FastAPI()

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def handle_exception(e):
    return JSONResponse(status_code=500, content={"message": f"Произошла неизвестная ошибка: {e}"})


@app.get("/organizations/by_building_address/",
         description="Получает организации, связанные с указанным адресом здания")
async def get_organizations_by_building_address(address: str, db: AsyncSession = Depends(get_db)):
    try:
        # Получаем здание по адресу
        building_query = select(Building).where(Building.address == address)
        result = await db.execute(building_query)
        building = result.scalars().first()
        if not building:
            return JSONResponse(status_code=404, content={"message": "Здание не найдено"})

        # Получаем организации, связанные с найденным зданием
        organizations_query = select(Organization).where(Organization.building_id == building.id)
        organizations_result = await db.execute(organizations_query)
        organizations = organizations_result.scalars().all()
        if not organizations:
            return JSONResponse(status_code=404, content={"message": "Организация не найдена"})

        return {"organizations": [org.name for org in organizations]}
    except Exception as e:
        return handle_exception(e)


@app.get("/organizations/by_activity_name/",
         description="Получает организации, связанные с указанным именем активности.")
async def get_organizations_by_activity_name(activity_name: str, db: AsyncSession = Depends(get_db)):
    try:
        # Получаем активность по имени
        activity_query = select(Activity).where(Activity.name == activity_name)
        activity_result = await db.execute(activity_query)
        activity = activity_result.scalars().first()
        if not activity:
            return JSONResponse(status_code=404, content={"message": "Активность не найдена"})

        # Получаем организации, связанные с активностью
        organizations_query = select(OrganizationActivity).where(OrganizationActivity.activity_id == activity.id)
        organizations_result = await db.execute(organizations_query)
        organizations = organizations_result.scalars().all()

        return {"organizations": [org.organization.name for org in organizations]}
    except Exception as e:
        return handle_exception(e)


@app.get("/organizations/by_area/",
         description="Получает здания, расположенные в указанной области на основе координат здания и разницы широты и "
                     "долготы от этих координат")
async def get_organizations_by_area(latitude: float, longitude: float, lat_diff: float, lon_diff: float,
                                     db: AsyncSession = Depends(get_db)):
    try:
        # Определяем границы поиска зданий
        min_latitude = latitude - lat_diff
        max_latitude = latitude + lat_diff
        min_longitude = longitude - lon_diff
        max_longitude = longitude + lon_diff

        # Получаем здания по координатам
        query = select(Building).where(
            Building.latitude.between(min_latitude, max_latitude),
            Building.longitude.between(min_longitude, max_longitude)
        )
        result = await db.execute(query)
        buildings = result.scalars().all()

        return {"buildings": [{"id": b.id, "address": b.address} for b in buildings]}
    except Exception as e:
        return handle_exception(e)


@app.get("/organization/{org_id}/",
         description="Получает детали конкретной организации по её ID")
async def get_organization(org_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Получаем организацию по ID
        organization_query = select(Organization).where(Organization.id == org_id)
        result = await db.execute(organization_query)
        organization = result.scalars().first()
        if not organization:
            return JSONResponse(status_code=404, content={"message": "Организация не найдена"})

        # Получаем адрес организации
        address_query = select(Building).where(Building.id == organization.building_id)
        address_result = await db.execute(address_query)
        address = address_result.scalars().first()

        return {
            "id": organization.id,
            "name": organization.name,
            "address": address.address if address else None,
            "phone_numbers": [pn.number for pn in organization.phone_numbers]
        }
    except Exception as e:
        return handle_exception(e)


@app.get("/organizations/search_by_activity/",
         description="Ищет организации, связанные с активностями, включая подактивности")
async def search_organizations_by_activity(activity_name: str, db: AsyncSession = Depends(get_db)):
    activities_to_search = []

    async def find_subactivities(activity, level):
        if activity:
            activities_to_search.append(activity)
            query = select(Activity).where(Activity.parent_id == activity.id)
            sub_activities = await db.execute(query)
            sub_activities_list = sub_activities.scalars().all()
            if level <= 3:
                for sub_activity in sub_activities_list:
                    await find_subactivities(sub_activity, level + 1)

    try:
        root_query = select(Activity).where(Activity.name == activity_name)
        root_result = await db.execute(root_query)
        root_activity = root_result.scalars().first()

        if root_activity:
            await find_subactivities(root_activity, 1)

        organizations = set()
        for activity in activities_to_search:
            query = select(OrganizationActivity).where(OrganizationActivity.activity_id == activity.id)
            orgs_result = await db.execute(query)
            orgs = orgs_result.scalars().all()
            organizations.update(org.organization for org in orgs)

        return {"organizations": [org.name for org in organizations]}
    except Exception as e:
        return handle_exception(e)


@app.get("/organizations/search_by_name/",
         description="Ищет организации, имена которых содержат указанную строку")
async def search_organizations_by_name(name: str, db: AsyncSession = Depends(get_db)):
    try:
        # Производим поиск организаций по имени
        query = select(Organization).where(Organization.name.ilike(f"%{name}%"))
        result = await db.execute(query)
        organizations = result.scalars().all()

        return {"organizations": [{
            "id": organization.id,
            "name": organization.name,
            "address": organization.building.address if organization.building else None,
            "phone_numbers": [pn.number for pn in organization.phone_numbers]
        } for organization in organizations]}
    except Exception as e:
        return handle_exception(e)


@app.post("/create_building/",
          description="Создает новую запись о здании с указанным адресом и координатами")
async def create_building(address: str, latitude: float, longitude: float, db: AsyncSession = Depends(get_db)):
    try:
        # Создаем новое здание
        new_building = Building(address=address, latitude=latitude, longitude=longitude)
        db.add(new_building)
        await db.commit()
        await db.refresh(new_building)
        return {"id": new_building.id, "message": "Здание успешно создано"}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)


@app.post("/create_organization/",
          description="Создает новую организацию с указанными данными")
async def create_organization(name: str, address: str, phone_numbers: list[str], activities: list[str],
                              db: AsyncSession = Depends(get_db)):
    try:
        # Находим здание по адресу
        building_query = select(Building).where(Building.address == address)
        building_result = await db.execute(building_query)
        building = building_result.scalars().first()

        if not building:
            return JSONResponse(status_code=404, content={"message": "Здание не найдено"})

        # Создаем новую организацию
        new_organization = Organization(name=name, building_id=building.id)
        db.add(new_organization)
        await db.commit()
        await db.refresh(new_organization)

        # Добавляем телефонные номера
        for number in phone_numbers:
            phone_number = PhoneNumber(number=number, organization_id=new_organization.id)
            db.add(phone_number)

        # Добавляем активности
        for activity_name in activities:
            activity_query = select(Activity).where(Activity.name == activity_name)
            activity_result = await db.execute(activity_query)
            activity = activity_result.scalars().first()
            if activity:
                org_activity = OrganizationActivity(organization_id=new_organization.id, activity_id=activity.id)
                db.add(org_activity)

        await db.commit()
        return {"id": new_organization.id, "name": new_organization.name}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)


@app.post("/activities/",
          summary="Создать новую активность",
          description="Создает новую активность, возможно, под родительской активностью")
async def create_activity(name: str, parent_id: int = None, db: AsyncSession = Depends(get_db)):
    try:
        # Проверяем уровень родительской активности, если она указана
        if parent_id is not None:
            parent_activity_query = select(Activity).where(Activity.id == parent_id)
            parent_activity_result = await db.execute(parent_activity_query)
            parent_activity = parent_activity_result.scalars().first()

            if parent_activity and parent_activity.level >= 3:
                return JSONResponse(status_code=400,
                                    content={"message": "Нельзя создать активность глубиной больше трёх"})

        # Создаем новую активность
        new_activity = Activity(name=name, parent_id=parent_id)
        db.add(new_activity)
        await db.commit()
        await db.refresh(new_activity)
        return {"id": new_activity.id, "name": new_activity.name}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)