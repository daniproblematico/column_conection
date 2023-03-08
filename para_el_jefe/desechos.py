for n in levels:
    # for each column in the level
    for i in levels[n]["key_cols"]:
        connected_element = {}
        section = {}
        if i in columns.keys():
            section[i + n] = dict(level_id=n, id=i, connected_elements=connected_element)
            columns[i]["sections"].update(section[i + n])
        else:
            section[i + n] = dict(level_id=n, id=i, connected_elements=connected_element)
            columns[i] = dict(sections=section)

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
                column_node_coordinates = [
                    levels[n]["nodes"][levels[n]["info_cols"][i]["node_j"]]["x_coord"],
                    levels[n]["nodes"][levels[n]["info_cols"][i]["node_j"]]["y_coord"],
                ]
                # calcules the lenght and angle of the beam connected to the column
                beam_lenght = calculate_lenght(
                    beam_nodei_coordinates,
                    beam_nodej_coordinates,
                )

                #saved_beams[j] = extract_element(n, j, "seccion", "refuerzo", beam_lenght)
                angle = calculate_angle(
                    beam_nodei_coordinates,
                    beam_nodej_coordinates,
                    column_node_coordinates,
                )
                con="con"
                # stores the information of the beam connected to the column
                connected_element[j] = extract_element(n,j,con,angle,"sect","ref",beam_lenght)

