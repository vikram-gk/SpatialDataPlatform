from db import database
from bson import ObjectId
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(tags=["MultiPoint APIs"])
multi_point_coll = database["MultiPoints"]
database.MultiPoints.create_index([("location", "2dsphere")])


class MultiPoint(BaseModel):
    name: str
    coordinates: List[List[float]]  # List of [longitude, latitude] pairs


class MultiPointUpdate(BaseModel):
    filter_id: Optional[str] = Field(None, description="Filter by document ID")
    filter_name: Optional[str] = Field(None, description="Filter by name")
    filter_coordinates: Optional[List[List[float]]] = Field(None, description="Filter by MultiPoint coordinates")
    new_name: Optional[str] = Field(None, description="New name for the MultiPoint")
    new_coordinates: Optional[List[List[float]]] = Field(None, description="New coordinates for the MultiPoint")


@router.post('/addMultiPoint')
async def add_multi_point(multi_point: MultiPoint):
    """
        This is an API to add a MultiPoint(a spatial datastructure consisting of multiple points).
        This API receives two params:
        :param name: which is the name of the MultiPoint
        :param coordinates: which are the coordinates of this MultiPoint in [list[list[float]]] structure
        :return: This parameter returns if there are any errors in the input params or the 'id' if the data is added to
        the MultiPoint Database
        """
    try:
        multi_point_data = {
            "name": multi_point.name,
            "location": {
                "type": "MultiPoint",
                "coordinates": multi_point.coordinates
            }
        }
        result = multi_point_coll.insert_one(multi_point_data)
        return {"id": str(result.inserted_id), "message": "multi_point_data has been added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while adding the multi-point data:\n{str(e)}")


@router.get('/getMultiPoints')
async def get_multi_points(
        name: Optional[str] = Query(description="Name to search for"),
        coordinates: Optional[List[float]] = Query(example=[77.5946, 12.9716]),
        radius: float = Query(1000,
                        description="Radius (in meters) to search around the coordinates if no exact match is found")
):
    """
       This is an API to fetch the MultiPoint data from the MultiPoint database if the input criteria is matched
       :param name: a name filter to find based on the name of the MultiPoint
       :param coordinates: coordinates filter to search upon
       :param radius: to check whether there are any coordinates found in the surrounding input radius
       :return: This API returns of any documents matches either of the mentioned filters
       """
    try:
        if not coordinates and not name:
            raise HTTPException(status_code=400, detail="Either 'coordinates' or 'name' must be provided.")

        if name:
            query_name = {"name": name}
            name_match = list(multi_point_coll.find(query_name, {"_id": 0}))

            if name_match:
                return {"multi_points": name_match}
            else:
                raise HTTPException(status_code=404, detail="No matching document found for the given name")

        if coordinates:
            if len(coordinates) != 2:
                raise HTTPException(status_code=400,
                                    detail="Coordinates must be a list with two values: [longitude, latitude]")

            query_exact = {"location.coordinates": {"$elemMatch": {"$eq": coordinates}}}
            exact_match = list(multi_point_coll.find(query_exact, {"_id": 0}))

            if exact_match:
                return {"multi_points": exact_match}

            query_nearby = {
                "location": {
                    "$geoWithin": {
                        "$centerSphere": [
                            coordinates,
                            radius / 6378137.0  # Convert radius to radians (radius of Earth in meters)
                        ]
                    }
                }
            }

            nearby_points = list(multi_point_coll.find(query_nearby, {"_id": 0}))

            if not nearby_points:
                raise HTTPException(status_code=404, detail="No matching document found for the given coordinates")

            return {"multi_points": nearby_points}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the multi-points: {str(e)}")


@router.put('/updateMultiPoint')
async def update_multi_point(multi_point_update: MultiPointUpdate):
    """
       This is an API to update any of the existing MultiPoint document already existing in the database
       :param multi_point_update: The input parameters required for searching the documents based on filter fields and
       update corresponding to the update fields
       :return: Returns if the API fails in any stage with an appropriate error message or success message
       """
    try:
        if (not multi_point_update.filter_id and not multi_point_update.filter_name and
                not multi_point_update.filter_coordinates):
            raise HTTPException(status_code=400,
                                detail="At least one of filter_id, filter_name, or filter_coordinates must be provided "
                                       "to identify the document to update")

        if not multi_point_update.new_name and not multi_point_update.new_coordinates:
            raise HTTPException(status_code=400,
                                detail="At least one of new_name or new_coordinates must be provided to update")

        query = {}
        if multi_point_update.filter_id:
            query["_id"] = ObjectId(multi_point_update.filter_id)
        if multi_point_update.filter_name:
            query["name"] = multi_point_update.filter_name
        if multi_point_update.filter_coordinates:
            query["location.coordinates"] = multi_point_update.filter_coordinates

        update_data = {}
        if multi_point_update.new_name:
            update_data["name"] = multi_point_update.new_name
        if multi_point_update.new_coordinates:
            update_data["location"] = {
                "type": "MultiPoint",
                "coordinates": multi_point_update.new_coordinates
            }

        result = multi_point_coll.update_one(query, {"$set": update_data})

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="No matching document found for the given criteria")

        return {"message": "MultiPoint data has been updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the MultiPoint data: {str(e)}")
