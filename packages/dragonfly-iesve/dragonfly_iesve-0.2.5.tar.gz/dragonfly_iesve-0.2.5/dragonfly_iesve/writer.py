# coding: utf-8
"""Write a gem file from a Dragonfly model."""
from __future__ import division

from ladybug_geometry.geometry3d import Polyface3D
from honeybee.facetype import Floor, RoofCeiling, face_types
from honeybee.room import Room as HBRoom
from honeybee_ies.writer import model_to_gem as hb_model_to_gem


def model_to_gem(model, use_multiplier=True, exclude_plenums=False, merge_method='None'):
    """Generate an IES GEM string from a Dragonfly Model.

    Args:
        model: A dragonfly Model.
        use_multiplier: Boolean to note whether the multipliers on each Building
            story will be passed along to the Room objects or if full geometry
            objects should be written for each repeated story in the
            building. (Default: True).
        exclude_plenums: Boolean to indicate whether ceiling/floor plenum depths
            assigned to Room2Ds should generate distinct 3D Rooms in the
            translation. (Default: False).
        merge_method: An optional text string to describe how the Room2Ds should
            be merged into individual Rooms during the translation. Specifying a
            value here can be an effective way to reduce the number of Room volumes
            in the resulting Model and, ultimately, yield a faster simulation time
            with less results to manage. Note that Room2Ds will only be merged if they
            form a contiguous volume across their solved adjacencies. Otherwise,
            there will be multiple Rooms per zone or story, each with an integer
            added at the end of their identifiers. Choose from the following options:

            * None - No merging of Room2Ds will occur
            * Zones - Room2Ds in the same zone will be merged
            * PlenumZones - Only plenums in the same zone will be merged
            * Stories - Rooms in the same story will be merged
            * PlenumStories - Only plenums in the same story will be merged

    Returns:
        Path to exported GEM file.
    """
    # translate the model to honeybee
    hb_model = model.to_honeybee(
        'District', use_multiplier=use_multiplier, exclude_plenums=exclude_plenums,
        solve_ceiling_adjacencies=False, merge_method=merge_method,
        enforce_adj=False, enforce_solid=True
    )[0]

    # check if there are any ceiling/floor air boundaries to translate
    cf_air_rooms = []
    for room in model.room_2ds:
        if not room.has_floor or not room.has_ceiling:
            cf_air_rooms.append(room)

    # if any floor/ceiling rooms were found, solve adjacency between them
    if len(cf_air_rooms) != 0:
        tolerance = model.tolerance
        room_ids = [r.identifier for r in cf_air_rooms]
        has_floor_ceil = [(r.has_floor, r.has_ceiling) for r in cf_air_rooms]
        hb_rooms = hb_model.rooms_by_identifier(room_ids)
        # intersect the Rooms with one another for matching adjacencies
        HBRoom.intersect_adjacency(hb_rooms, tolerance, model.angle_tolerance)
        # solve adjacencies between rooms to yield matching air boundaries
        for i, (room_1, fc_1) in enumerate(zip(hb_rooms, has_floor_ceil)):
            try:
                for room_2, fc_2 in zip(hb_rooms[i + 1:], has_floor_ceil[i + 1:]):
                    if not Polyface3D.overlapping_bounding_boxes(
                            room_1.geometry, room_2.geometry, tolerance):
                        continue  # no overlap in bounding box; adjacency impossible
                    for face_1 in room_1._faces:
                        for face_2 in room_2._faces:
                            if face_1.geometry.is_centered_adjacent(
                                    face_2.geometry, tolerance):
                                face_1.remove_sub_faces()
                                face_2.remove_sub_faces()
                                hf_1, hc_1 = fc_1
                                hf_2, hc_2 = fc_2
                                if not hc_1 and not hf_2:
                                    if isinstance(face_1.type, RoofCeiling) and \
                                            isinstance(face_2.type, Floor):
                                        face_1.type = face_types.air_boundary
                                        face_2.type = face_types.air_boundary
                                if not hf_1 and not hc_2:
                                    if isinstance(face_2.type, RoofCeiling) and \
                                            isinstance(face_1.type, Floor):
                                        face_1.type = face_types.air_boundary
                                        face_2.type = face_types.air_boundary
                                break
            except IndexError:
                pass  # we have reached the end of the list of zones

    # return the honeybee model translated to GEM
    return hb_model_to_gem(hb_model)
