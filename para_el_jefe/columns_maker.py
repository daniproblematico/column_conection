import json
import numpy as np

# prodes_data = open("project.prodes", "r")

# Auxiliar functions
def beam_finder(element_id, levels):
    """Search what level the element is in

    Args:
        element_id (str): element id
        levels (dict): dictionary with all the levels information processed

    Returns:
        list: list that contains the levels where the element is found
    """
    encontrados = []
    for level in levels:
        if (
            element_id in levels[level]["key_beams"]
            or element_id in levels[level]["key_nodes"]
            or element_id in levels[level]["key_cols"]
        ):
            encontrados.append(level)

    return encontrados


def column_verify(item, columns, levels_info):
    """Search what column the element is in, what level it is in, and the elements that are in the same column

    Args:
        item (str): element to be searched
        columns (dict): dictionary with all the columns information processed
        levels_info (dict): dictionary with all the levels information processed

    Returns:
        list: list that contains the levels where the element is found
        str: column id
        dict: dictionary with all the keys elements in the same column
    """
    item_level = beam_finder(item, levels_info)
    for i, banos in enumerate(columns):
        if item in columns[i]:
            return (item_level, i, columns[i].keys())


# Essential functions


def read_file(file):
    """Reads the file and returns the information as a dictionary

    Args:
        file (geom): file path

    Returns:
        dict: dictionary with all the information of the building
    """
    with open(file, "r") as f:
        building_data = json.load(f)

    return building_data


def create_node(id, global_info_nodes, story_heigth_acum, new_id):
    """Node information constructor

    Args:
        id (string): Node id
        global_info_nodes (dict): Coordinates information of all nodes
        story_heigth_acum (float): Height of the current level

    Returns:
        info_node: Dictionary with node information
    """

    info_node = dict(
        prev_id=id,
        x_coord=global_info_nodes[id][0],
        y_coord=global_info_nodes[id][1],
        z_coord=story_heigth_acum
        if len(global_info_nodes[id]) == 2
        else global_info_nodes[id][2],
        new_id=new_id,
    )

    return info_node


def calculate_lenght(element_nodei_coordinates, element_nodej_coordinates):
    """calculates the length of an element on the x-y plane

    Args:
        beam_nodei_coordinates (list): coordinates of the node i of the beam in the order [x,y]
        beam_nodej_coordinates (list): coordinates of the node j of the beam in the order [x,y]

    Returns:
        beam_lenght: length of the beam
    """

    # Calculates the length of the beam using pitagoras theorem
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
    """calculates the angle between a beam element and the referency vector using dot product

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


def extract_element(
    level,
    element_id,
    beam_id,
    orientation,
    area,
    reinforcement,
    length,
):

    """Creates a dictionary with the information of the beam element

    Args:
        levels (dict): contains all the informatios of the building by level
        element_id (string): id of the element
        beam_id (string): id of the beam
        orientation (float): orientation of the beam in radians clockwise respect to the x axis
        area (list): area of the beam in the order [b,h]
        reinforcement (string): reinforcement of the beam
        length (float): length of the beam

    Returns: dictionary with the information of the beam
    """

    return dict(
        element_id=element_id,
        beam_id=beam_id,
        orientation=orientation,
        area=area,
        reinforcement=reinforcement,
        length=length,
        level_id=level,
    )


def extract_levels(data, initial_heigth):
    """Extracts the information of the levels making them keys in the dictionary Levels

    Args:
        data (dict): contains all the informatios of the building from the json file
        initial_heigth (float): reference height of the building

    Returns:
        levels: dictionary with the information organized by level
    """
    # Dictionary that will contain all the information of the building
    levels = {}
    # Node arbitrary identificator
    nodes_id = 0
    # For each level, the information will be storaged
    for story in reversed(data["pisos"]):
        # Define keys for the levels dict
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

                for j, node in enumerate(
                    [info_element["node_i"], info_element["node_j"]]
                ):
                    # Check if node is already storaged
                    if node in levels[story]["nodes"]:
                        continue
                    # Check if it is a column node, only will be storaged final node
                    if type_element == "cols" and not j:
                        continue

                    # Creates the element node
                    levels[story]["nodes"][node] = create_node(
                        node,
                        data["nodos"],
                        levels[story]["story_heigth_acum"],
                        str(nodes_id),
                    )
                    nodes_id += 1
                    # Add the node to the list of nodes of the level
                    levels[story]["key_nodes"].append(node)
    return levels


def columns_assembler(elements, tolerance):
    """find the vertical elements that are connected and assign them to a column with arbitrary name

    Args:
        elements (dict): dictionary with spatial information of the vertical elements
    Returns:
        columns: dictionary with the information organized by column
    """

    # dictionary where the columns will be storaged and the namer of the columns
    columns = {}
    namer = 0

    # for each element, the elements in the same coordinates will be storaged in a list
    for i in elements:
        columns[namer] = {}
        node_connector = elements[i]["node_t"]
        for j in elements:
            if (
                abs(elements[j]["node_t"]["x_coord"] - node_connector["x_coord"])
                < tolerance
                and abs(elements[j]["node_t"]["y_coord"] - node_connector["y_coord"])
                < tolerance
            ):
                columns[namer].update({j: elements[j]})
        namer += 1

    # there will be repeated columns, this will be deleted to avoid errors
    for i in columns:
        repeated_elements = 0
        for j in columns:
            if set(columns[i]) == set(columns[j]):
                repeated_elements += 1
            if repeated_elements > 1:
                columns[j].clear()

    for empty in list(columns):
        if not columns[empty]:
            del columns[empty]

    return columns


def export_data(name, data):
    """export data to a json file

    Args:
        name (string): name of the file
        data (dict): data to be exported
    """
    with open(name, "w") as fp:
        json.dump(data, fp)


# prodes functions
def element_finder(element, prodes_data, element_type):
    """this function will find what actual element this element came from using prodes file infor

    Args:
        element (String): Name of the element
        prodes_data (txt?): file with actual elements information
        element_type (String): What kind of actual element i'm interested in ("V-" for Beams, "C-" for columns, "N-" for nervs)

    Return: sorage: actual element id
    """

    searcher = False
    for i in prodes_data:
        if searcher == True:
            if element in i:
                storage = beam
                break
            else:
                searcher = False

        if element_type in i:
            searcher = True
            beam = i
    return storage


###############
# Main script #

building_data = read_file("midas.geom")

levels = extract_levels(building_data, 0)

vertical_elements = {}

for n in levels:
    # for each column in the level
    for i in levels[n]["key_cols"]:

        if i not in vertical_elements.keys():
            v_element_node = levels[n]["nodes"][levels[n]["info_cols"][i]["node_j"]]
            connected_elements = {}
            vertical_elements[i] = dict(
                connected_elements=connected_elements,
                node_t=v_element_node,
                level_id=n,
            )
        else:
            v_element_node = levels[n]["nodes"][levels[n]["info_cols"][i]["node_j"]]
            connected_elements = {}
            vertical_elements[i + n] = dict(
                connected_elements=connected_elements,
                node_t=v_element_node,
                level_id=n,
            )
        # for each beam
        for j in levels[n]["key_beams"]:

            # check if the beam is connected to the column
            if (
                levels[n]["info_cols"][i]["node_j"]
                in levels[n]["info_beams"][j]["connectivity"]
            ):

                # extract the geometric information of the beam connected to the column
                beam_nodei_coordinates = [
                    levels[n]["nodes"][levels[n]["info_beams"][j]["node_i"]]["x_coord"],
                    levels[n]["nodes"][levels[n]["info_beams"][j]["node_i"]]["y_coord"],
                ]
                beam_nodej_coordinates = [
                    levels[n]["nodes"][levels[n]["info_beams"][j]["node_j"]]["x_coord"],
                    levels[n]["nodes"][levels[n]["info_beams"][j]["node_j"]]["y_coord"],
                ]
                v_element_node_coordinates = [
                    v_element_node["x_coord"],
                    v_element_node["y_coord"],
                ]
                # calcules the length and angle of the beam connected to the column
                beam_lenght = calculate_lenght(
                    beam_nodei_coordinates,
                    beam_nodej_coordinates,
                )

                angle = calculate_angle(
                    beam_nodei_coordinates,
                    beam_nodej_coordinates,
                    v_element_node_coordinates,
                )
                con = "this info will come from the prodes file"
                # stores the information of the beam connected to the column
                connected_elements[j] = extract_element(
                    n,
                    j,
                    con,
                    angle,
                    "b*h, this info will come from a prodes file",
                    "this will come from a prodes file",
                    beam_lenght,
                )


building_columns = columns_assembler(vertical_elements, 0.001)

# This is the way to verify if the columns are correct
# Element
item = "B12355"

# elements
print(column_verify(item, building_columns, levels))

# guardar building_columns en un archivo json

export_data("building_columns_midas.json", building_columns)

