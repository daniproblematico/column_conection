import json
import numpy as np

with open("project.geom", "r") as f:
    building_data = json.load(f)
    print(type(building_data))

levels = {}
acumulator_heigths = 0


def create_node(id, global_info_nodes, story_heigth_acum):
    """Node information constructor

    Args:
        id (string): Node id
        global_info_nodes (dict): Coordinates information of all nodes
        story_heigth_acum (float): Height of the current level

    Returns:
        info_node: Dictionary with node information
    """

    info_node = dict(
        id=id,
        x_coord=global_info_nodes[id][0],
        y_coord=global_info_nodes[id][1],
        z_coord=story_heigth_acum
        if len(global_info_nodes[id]) == 2
        else global_info_nodes[id][2],
    )

    return info_node

def calculate_lenght(element_nodei_coordinates, element_nodej_coordinates):
    """calculates the lenght of an element on the x-y plane

    Args:
        beam_nodei_coordinates (list): coordinates of the node i of the beam in the order [x,y]
        beam_nodej_coordinates (list): coordinates of the node j of the beam in the order [x,y]

    Returns:
        beam_lenght: lenght of the beam
    """

    # calculates the lenght of the beam using pitagoras theorem
    element_lenght = np.sqrt(
        (element_nodej_coordinates[1] - element_nodei_coordinates[1]) ** 2
        + (element_nodej_coordinates[0] - element_nodei_coordinates[0]) ** 2
    )

    return element_lenght

def calculate_angle(
    beam_nodei_coordinates,
    beam_nodej_coordinates,
    column_node_coordinates,
):
    """calculates the angle between the beam and the referency vector using the dot product

    Args:
        beam_nodei_coordinates (list): coordinates of the node i of the beam in the order [x,y]
        beam_nodej_coordinates (list): coordinates of the node j of the beam in the order [x,y]
        column_node_coordinates (list): coordinates of the node of the column in the order [x,y]

    Returns:
        angle: angle between the beam and the referency vector of the x axis in radians clockwise
    """

    # creates the normal vector to the beam
    x_coord_diference = (
        beam_nodej_coordinates[0]
        + beam_nodei_coordinates[0]
        - 2 * column_node_coordinates[0]
    )
    y_coord_diference = (
        beam_nodej_coordinates[1]
        + beam_nodei_coordinates[1]
        - 2 * column_node_coordinates[1]
    )

    # calculates the angle between the normal vector and the referency vector
    referency_vector = [1, 0]
    normal_vector = np.array([x_coord_diference, y_coord_diference])
    referency_vector = np.array(referency_vector)
    angle = np.arccos(
        np.dot(normal_vector, referency_vector)
        / (np.linalg.norm(normal_vector) * np.linalg.norm(referency_vector))
    )

    # if the normal vector is in the second or third quadrant, the angle is corrected
    if y_coord_diference < 0:
        angle = 2 * np.pi - angle

    return angle

def extraer_viga(level, beam_id, section, reinforcement,  lenght):

    """Extracts the information of the beams making them objects of the class Beam

    Args:
        levels (dict): contains all the informatios of the building by level
        beam_id (string): id of the beam
        section (string): section of the beam
        reinforcement (string): reinforcement of the beam
        lenght (float): lenght of the beam
    """
    return dict(
        id=beam_id,
        section=section,
        reinforcement=reinforcement,
        lenght=lenght,
        level_id=level,
    )

def extract_levels(data,initial_heigth):
    """Extracts the information of the levels making them objects of the class Level

    Args:
        data (dict): contains all the informatios of the building from the json file
        initial_heigth (float): initial heigth of the building

    Returns:
        levels: dictionary with the information organized by level
    """
    levels = {}
    # For each level, the information will be storaged
    for story in reversed(data["pisos"]):
    # define keys for the levels dict
        levels[story] = dict(
        id=story,
        key_nodes=[],
        key_cols=list(data["col_piso"][story].keys()),
        key_beams=list(data["vig_piso"][story].keys()),
        story_heigth=data["pisos"][story],
        story_heigth_acum=initial_heigth + data["pisos"][story],
        info_cols={},
        info_beams={},
        nodes={},
    )
        initial_heigth += data["pisos"][story]

    # For each element type, element information will be storaged
        for type_element in ["cols", "beams"]:
        # Key name from the data dict
            list_to_iterate = levels[story][f"key_{type_element}"]
        # Original name of the key in the data dict
            original_key_name = "columnas" if type_element == "cols" else "vigas"

        # For each element in the list, the information will be storaged
            for element in list_to_iterate:
                info_element = dict(
                id=element,
                connectivity=data[original_key_name][element],
                node_i=data[original_key_name][element][0],
                node_j=data[original_key_name][element][1],
            )

            # By element type, the information will be storaged
                if type_element == "cols":
                    levels[story]["info_cols"][element] = info_element
                elif type_element == "beams":
                    levels[story]["info_beams"][element] = info_element

                for j, node in enumerate([info_element["node_i"], info_element["node_j"]]):
                # Check if node is already storaged
                    if node in levels[story]["nodes"]:
                        continue
                # Check if it is a column node, only will be storaged final node
                    if type_element == "cols" and not j:
                        continue
                    
                    # Creates the element node
                    levels[story]["nodes"][node] = create_node(
                    node, data["nodos"], levels[story]["story_heigth_acum"]
                )
                    # Add the node to the list of nodes of the level
                    levels[story]["key_nodes"].append(node)
    return(levels)

levels=extract_levels(building_data,0)

columns = {}
saved_beams = {}
for n in levels:
    # for each column in the level
    for i in levels[n]["key_cols"]:
        connected_beam = {}
        trame={}
        if i in columns.keys():
            trame[i+n] = dict(level_id=n, id=i,connected_beams=connected_beam)
            columns[i]['trames'].update(trame[i+n])
        else:
            trame[i+n] = dict(level_id=n, id=i,connected_beams=connected_beam)
            columns[i] = dict(trames=trame)
            


        # for each beam
        for j in levels[n]["key_beams"]:

            # extract the geometric information of the beam connected to the column
            beam_nodei_coordinates = [
                levels[n]["nodes"][levels[n]["info_beams"][j]["node_i"]]["x_coord"],
                levels[n]["nodes"][levels[n]["info_beams"][j]["node_i"]]["y_coord"],
            ]
            beam_nodej_coordinates = [
                levels[n]["nodes"][levels[n]["info_beams"][j]["node_j"]]["x_coord"],
                levels[n]["nodes"][levels[n]["info_beams"][j]["node_j"]]["y_coord"],
            ]
            column_node_coordinates = [
                levels[n]["nodes"][levels[n]["info_cols"][i]["node_j"]]["x_coord"],
                levels[n]["nodes"][levels[n]["info_cols"][i]["node_j"]]["y_coord"],
            ]
            # calcules the lenght and angle of the beam connected to the column
            beam_lenght = calculate_lenght(
                beam_nodei_coordinates,
                beam_nodej_coordinates,
            )

            saved_beams[j]=extraer_viga(n, j, "seccion", "refuerzo", beam_lenght)
            
            # check if the beam is connected to the column
            if (
                levels[n]["info_cols"][i]["node_j"]
                in levels[n]["info_beams"][j]["connectivity"]
            ):
                angle = calculate_angle(
                    beam_nodei_coordinates,
                    beam_nodej_coordinates,
                    column_node_coordinates,
            )
                # stores the information of the beam connected to the column
                connected_beam[j] = dict(
                    beam_id=j,
                    orientacion=angle,
                )


print(columns)
x = 2
