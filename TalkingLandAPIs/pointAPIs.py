from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from db import database
from bson import ObjectId
from typing import Optional

rout = APIRouter(tags=["Point APIs"])
point_coll = database["Point"]
database.Point.create_index([("location", "2dsphere")])


class Point(BaseModel):
    name: str
    type: str = Field(default="Point")
    coordinates: list[float] = Field(..., example=[18.8910, 17.67687])


class PointUpdate(BaseModel):
    filter_id: Optional[str] = None
    filter_name: Optional[str] = None
    filter_coordinates: Optional[list[float]] = None

    new_name: Optional[str] = None
    new_coordinates: Optional[list[float]] = None


@rout.post('/addPoint')
async def add_point(point: Point):
    try:
        point_data = {
            "name": point.name,
            "location": {
                "type": "Point",
                "coordinates": point.coordinates
            }
        }
        result = point_coll.insert_one(point_data)
        # print({"id": str(result.inserted_id), "point_data": point_data})
        return {"id": str(result.inserted_id), "message": "point_data has been added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while adding the point data:\n{str(e)}")


@rout.get('/getPoints')
async def get_points(
        name: str = Query(None, description="Name to search for"),
        coordinates: list[float] = Query(None, example=[18.8910, 17.676879]),
        radius: float = Query(1000,
                        description="Radius (in meters) to search around the coordinates if no exact match is found")
):
    try:
        if not coordinates and not name:
            raise HTTPException(status_code=400, detail="Either 'coordinates' or 'name' must be provided.")

        # If name is provided, search based on the name
        if name:
            query_name = {"name": name}
            name_match = list(point_coll.find(query_name, {"_id": 0}))

            if name_match:
                return {"points": name_match}
            else:
                raise HTTPException(status_code=404, detail="No matching document found for the given name")

        # If coordinates are provided, search based on coordinates
        if coordinates:
            if len(coordinates) != 2:
                raise HTTPException(status_code=400,
                                    detail="Coordinates must be a list with two values: [longitude, latitude]")

            query_exact = {"location.coordinates": coordinates}
            exact_match = list(point_coll.find(query_exact, {"_id": 0}))

            if exact_match:
                return {"points": exact_match}

            # Perform a nearby search if no exact match is found
            query_nearby = {
                "location": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": coordinates
                        },
                        "$maxDistance": radius
                    }
                }
            }

            nearby_points = list(point_coll.find(query_nearby, {"_id": 0}))

            if not nearby_points:
                raise HTTPException(status_code=404, detail="No matching document found for the given coordinates")

            return {"points": nearby_points}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the points: {str(e)}")


@rout.put('/updatePoint')
async def update_point(point_update: PointUpdate):
    try:
        if not point_update.filter_id and not point_update.filter_name and not point_update.filter_coordinates:
            raise HTTPException(status_code=400,
                                detail="At least one of filter_id, filter_name, or filter_coordinates must be provided "
                                       "to identify the document to update")

        if not point_update.new_name and not point_update.new_coordinates:
            raise HTTPException(status_code=400,
                                detail="At least one of new_name or new_coordinates must be provided to update")

        query = {}
        if point_update.filter_id:
            query["_id"] = ObjectId(point_update.filter_id)
        if point_update.filter_name:
            query["name"] = point_update.filter_name
        if point_update.filter_coordinates:
            query["location.coordinates"] = point_update.filter_coordinates

        update_data = {}
        if point_update.new_name:
            update_data["name"] = point_update.new_name
        if point_update.new_coordinates:
            update_data["location"] = {
                "type": "Point",
                "coordinates": point_update.new_coordinates
            }

        result = point_coll.update_one(query, {"$set": update_data})

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="No matching document found for the given criteria")

        return {"message": "Point data has been updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the point data: {str(e)}")
