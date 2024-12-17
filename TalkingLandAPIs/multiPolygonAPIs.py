from db import database
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional


rout1 = APIRouter(tags=["MultiPolygonAPIs"])
multi_poly_coll = database["MultiplePolygon"]
database.MultiplePolygon.create_index([("location", "2dsphere")])


class MultiPolygon(BaseModel):
    name: str
    coordinates: List[List[List[List[float]]]]


class MultiPolygonUpdate(BaseModel):
    filter_id: Optional[str] = Field(None, description="Filter by document ID")
    filter_name: Optional[str] = Field(None, description="Filter by name")
    new_name: Optional[str] = Field(None, description="New name for the MultiPolygon")
    new_coordinates: Optional[List[List[List[List[float]]]]] = Field(None,
                                                                     description="New coordinates for the MultiPolygon")


@rout1.post("/addMultiPolygon")
async def add_multi_polygon(multipoly: MultiPolygon):
    """
    This is an API to add a multipolygon(a spatial datastructure consisting of multiple polygons).
    This API receives two params:
    :param name: which is the name of the multipolygon
    :param coordinates: which are the coordinates of this multipolygon in list[list[list[list[float]]]] structure
    :return: This parameter returns if there are any errors in the input params or the 'id' if the data is added to the
    MultiPolygon Database
    """
    try:
        multi_poly_data = {
            "name": multipoly.name,
            "location": {
                "type": "MultiPolygon",
                "coordinates": multipoly.coordinates
            }
        }

        result = multi_poly_coll.insert_one(multi_poly_data)
        return {"id": str(result.inserted_id), "message": "multi_poly_data has been added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while adding the multi-point data:\n{str(e)}")


@rout1.get("/getMultiPolygon")
async def get_multi_polygon(
        name: Optional[str] = Query(None, description="Name to search for"),
        coordinates: Optional[List[float]] = Query(None, example=[77.5946, 12.9716]),
        radius: float = Query(1000,
                        description="Radius (in meters) to search around the coordinates if no exact match is found")
):
    """
    This is an API to fetch the multipolygon data from the MultiPolygon database if the input criteria is matched
    :param name: a name filter to find based on the name of the multipolygon
    :param coordinates: coordinates filter to search upon
    :param radius: to check whether there are any coordinated found in the surrounding input radius
    :return: This API returns of any documents matches either of the mentioned filters
    """
    try:
        if not coordinates and not name:
            raise HTTPException(status_code=400, detail="Either 'coordinates' or 'name' must be provided.")

        if name:
            query_name = {"name": name}
            name_match = list(multi_poly_coll.find(query_name, {"_id": 0}))
            if name_match:
                return {"multi_polygons": name_match}

        if coordinates:
            if len(coordinates) != 2:
                raise HTTPException(status_code=400,
                                    detail="Coordinates must be a list with two values: [longitude, latitude]")

            query_exact = {
                "location.coordinates": {"$geoIntersects": {"$geometry": {"type": "Point", "coordinates": coordinates}}}}
            exact_match = list(multi_poly_coll.find(query_exact, {"_id": 0}))

            if exact_match:
                return {"multi_polygons": exact_match}

        query_nearby = {
            "location": {
                "$geoWithin": {
                    "$centerSphere": [
                        coordinates,
                        radius / 6378137.0
                    ]
                }
            }
        }

        nearby_polygons = list(multi_poly_coll.find(query_nearby, {"_id": 0}))

        if not nearby_polygons:
            raise HTTPException(status_code=404, detail="No matching document found for the given coordinates")

        return {"multi_polygons": nearby_polygons}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the multi-polygons: {str(e)}")


@rout1.put('/updateMultiplePolygon')
async def update_multiple_polygon(multi_polygon_update: MultiPolygonUpdate):
    """
    This is an API to update any of the existing multipolygon document already existing in the database
    :param multi_polygon_update: The input parameters required for searching the documents based on filter fields and
    update corresponding to the update fields
    :return: Returns if the API fails in any stage with an appropriate error message or success message
    """
    try:
        if not multi_polygon_update.filter_id and not multi_polygon_update.filter_name:
            raise HTTPException(status_code=400,
                                detail="At least one of filter_id or filter_name must be provided to identify the "
                                       "document to update")

        if not multi_polygon_update.new_name and not multi_polygon_update.new_coordinates:
            raise HTTPException(status_code=400,
                                detail="At least one of new_name or new_coordinates must be provided to update")

        query = {}
        if multi_polygon_update.filter_id:
            query["_id"] = ObjectId(multi_polygon_update.filter_id)
        if multi_polygon_update.filter_name:
            query["name"] = multi_polygon_update.filter_name

        update_data = {}
        if multi_polygon_update.new_name:
            update_data["name"] = multi_polygon_update.new_name
        if multi_polygon_update.new_coordinates:
            update_data["location"] = {
                "type": "MultiPolygon",
                "coordinates": multi_polygon_update.new_coordinates
            }

        result = multi_poly_coll.update_one(query, {"$set": update_data})

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="No matching document found for the given criteria")

        return {"message": "MultiPolygon data has been updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the multi-polygon data: {str(e)}")
