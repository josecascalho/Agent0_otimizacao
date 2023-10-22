import game_board as gb
import game_object as go
import socket
import sys
import random
import tkinter as tk
import json
import middleware.mysocket

class Server(BaseException):
    def __init__(self, host_ip, port_number, config):
        self.host = host_ip
        self.port = port_number
        self.server_socket = middleware.mysocket.Socket(host_ip, port_number)
        self.config = config
        self.player_dict = {}
        config["board_dimensions"] = (len(config["object_map"][0]), len(config["object_map"]))
        config["bomb_coordinates"], config["house_coordinates"], config["obstacle_coordinates"],config["players_coordinates"] = [], [], [], []
        config["weights"] = {}
        config["weightsignals"] = {}
        for row_index, row in enumerate(config["object_map"]):
            for char_index, char in enumerate(row):
                if char == "O":
                    config["obstacle_coordinates"].append((char_index, row_index))
                elif char == "I":
                    config["obstacle_coordinates"].append((char_index, row_index, "invisible"))
                elif char == "B":
                    config["bomb_coordinates"].append((char_index, row_index))
                elif char == "T":
                    config["house_coordinates"].append((char_index, row_index))
                elif char == "A":
                    config["players_coordinates"].append((char_index, row_index))

            for char_index, char in enumerate(config["weight_map"][row_index]):
                if char in "1234":
                    config["weights"][str(char_index)+","+str(row_index)] = config["weight_dictionary"][char]
                    config["weightsignals"][str(char_index)+","+str(row_index)] = char


        # Size of the world ...
        print("Starting the Game Board")
        columns, rows = config["board_dimensions"]

        self.root = tk.Tk()

        # Create gameboard
        self.board = gb.GameBoard(self.root, self.config, columns, rows)
        self.board.pack(side="top", fill="both", expand="true", padx=4, pady=4)

        # Initialize objects in the world
        self.initialize_weights()
        self.initialize_obstacles()
        self.initialize_goals()
        self.initialize_bombs()
        self.initialize_players()

        #self.player = go.Player('player', *self.config["start_position"], 'south', 'front', self.config)
        #self.player.set_home(self.config["start_position"])
        #self.player.close_eyes()
        #self.board.add(self.player, *self.config["start_position"])
        self.root.update()

    def initialize_obstacles(self):
        for i, obst in enumerate(self.config["obstacle_coordinates"]):
            ob = go.Obstacle('ob' + str(i), obst[0], obst[1], self.config, obst[-1] != "invisible")
            self.board.add(ob, obst[0], obst[1])

    def initialize_players(self):
        """
        A set of players. Each player has a number. We can ask for a specific player to move.
        """
        i = 1
        for p in self.config["players_coordinates"]:
            player = go.Player ('hospital' + str(i),i, p[0], p[1],'south','front', self.config)
            self.board.add(player, p[0], p[1])
            # Adding a player to DICT with key = player number
            self.player_dict[str(i)] = player
            i += 1
        # Test
        print(self.player_dict.values())

        #self.player = go.Player('player', *self.config["start_position"], 'south', 'front', self.config)
        #self.player.set_home(self.config["start_position"])
        #self.player.close_eyes()



    def initialize_goals(self):
        i = 1
        for g in self.config["house_coordinates"]:
            goal = go.Goal('house' + str(i), g[0], g[1], self.config)
            self.board.add(goal, g[0], g[1])
            i += 1


    def initialize_bombs(self):
        columns, rows = self.config["board_dimensions"][0], self.config["board_dimensions"][1]
        i = 1
        for b in self.config["bomb_coordinates"]:
            bomb = go.Bomb('bomb' + str(i), b[0], b[1], self.config)
            self.board.add(bomb, b[0], b[1])

            bomb_s = go.BombSound('bomb_sound_s' + str(i), b[0], (b[1]+1) % rows, self.config)
            self.board.add(bomb_s, b[0], (b[1]+1) % rows)

            bomb_s = go.BombSound('bomb_sound_e' + str(i), (b[0] + 1) % columns, b[1], self.config)
            self.board.add(bomb_s, (b[0] + 1) % columns, b[1])

            bomb_s = go.BombSound('bomb_sound_n' + str(i), b[0], (b[1] - 1) % rows, self.config)
            self.board.add(bomb_s, b[0], (b[1] - 1) % rows)

            bomb_s = go.BombSound('bomb_sound_w' + str(i), (b[0] - 1) % columns, b[1], self.config)
            self.board.add(bomb_s, (b[0] - 1) % columns, b[1])
            i += 1

    def initialize_weights(self):
        weights = {tuple([int(coord) for coord in k.split(",")]): float(v) for k, v in self.config["weights"].items()}
        # Test
        # print("Initialize weights:",weights)

        # numbers associated to the weights: not used
        # weight_signals = {tuple([int(coord) for coord in k.split(",")]): float(v) for k, v in self.config["weightsignals"].items()}


        images =["patch_clear","patch_lighter","patch_middle","patch_heavy"]
        patch = [[0]*self.board.columns]*self.board.rows
        # Get the max and min values in weights
        max_value = weights.get(max(weights,key=weights.get))
        min_value = weights.get(min(weights,key=weights.get))
        #Test
        # print("Max value:",max_value)
        # print("Min value:",min_value)

        # Normalize as step for four values
        step = (max_value - min_value) / 4.0
        keys = []
        # List of keys and dictionary of names
        for i in range(4):
             value = min_value + i* step
             keys.append( value )
        image=""
        # Test
        # print("Max columns:",self.board.columns)
        # print("Max rows:",self.board.rows)
        for column in range(0, self.board.columns):
            for row in range(0, self.board.rows):
                if (column, row) in weights:
                    weight = weights[(column,row)]
                    #weightsignal = weight_signals[(column,row)]
                else:
                    weight = random.uniform(min_value, max_value)
                # Selecting image version 1.0: selecting based on values
                if weight <= keys[1]: #weight >= keys[0]:
                    image = images[0]

                elif weight <= keys[2] and weight > keys[1]:
                    image = images[1]

                elif weight <= keys[3] and weight > keys[2]:
                    image = images[2]
                else:
                    image = images[3]
                # Selecting image version 2.0: selecting based on signals (1,2,3,4,R)
                # TODO

                patch[row][column] = go.Patch('patch' + str(column) + "-" + str(row), image, column, row,
                                                  weight, self.config)
                self.board.add(patch[row][column], column, row)
                #Teste
                #print("column:", column, "row:", row, "name:", n)



    def execute(self, cmd_type:str, value_type:str):
        res = ""
        if cmd_type == 'move':
            nr,res = value_type.split("_")
            self.player_dict[nr].close_eyes()
            pos = (self.player_dict[nr].get_x(),self.player_dict[nr].get_y())
            max_coord = self.board.get_max_coord()
            print(res[0])
            if int(res[0]) < max_coord[0] and int(res[1]) < max_coord[1]:
                if not self.board.is_target_obstacle(res) and not self.board.is_target_goal(res):
                    self.board.change_position(self.player_dict[nr],res[0], res[1])
            else:
                res = pos

        if cmd_type == 'command':
            nr,value = value_type.split("_")
            # -----------------------
            # movements without considering the direction
            # of the face of the object but testing the objects
            # -----------------------
            if value == 'north':

                self.player_dict[nr].close_eyes()
                pos = (self.player_dict[nr].get_x(),self.player_dict[nr].get_y())
                print("Position of player: ",nr," is ",pos)
                res = self.board.move_north(self.player_dict[nr],'forward')
                if not self.board.is_target_obstacle(res) and not self.board.is_target_goal(res):
                    self.board.change_position(self.player_dict[nr],res[0], res[1])
                else:
                    res = pos

            elif value == 'south':
                self.player_dict[nr].close_eyes()
                pos = (self.player_dict[nr].get_x(),self.player_dict[nr].get_y())
                res = self.board.move_south(self.player_dict[nr], 'forward')
                if not self.board.is_target_obstacle(res) and not self.board.is_target_goal(res):
                    self.board.change_position(self.player_dict[nr], res[0], res[1])
                else:
                    res = pos
            elif value == 'east':
                self.player_dict[nr].close_eyes()
                pos = (self.player_dict[nr].get_x(),self.player_dict[nr].get_y())
                res = self.board.move_east(self.player_dict[nr], 'forward')
                if not self.board.is_target_obstacle(res) and not self.board.is_target_goal(res):
                    self.board.change_position(self.player_dict[nr], res[0], res[1])
                else:
                    res = pos
            elif value == 'west':
                self.player_dict[nr].close_eyes()
                pos = (self.player_dict[nr].get_x(),self.player_dict[nr].get_y())
                res = self.board.move_west(self.player_dict[nr], 'forward')
                if not self.board.is_target_obstacle(res) and not self.board.is_target_goal(res):
                    self.board.change_position(self.player_dict[nr], res[0], res[1])
                else:
                    res = pos
            # -----------------------
            # move to home
            # -----------------------
            #elif value == 'home':
            #    res = self.board.move_home(self.player)



            elif value == "open_eyes":
                self.player_dict[nr].open_eyes()

            elif value == "close_eyes":
                res = self.player_dict[nr].close_eyes()
            elif value == "clean_board":
                res = self.board.clean_board()
            elif value == "bye" or value == "exit":
                self.server_socket.close()
                exit(1)
            else:
                pass
        elif cmd_type == 'info':
            value = value_type
            #if value == 'direction':
            #    res = self.player_dict[nr].get_direction()
            #if value == 'view':
            #    front = self.board.get_place_ahead(self.player)
            #    res = self.board.view_object(*front)
            #    res.reverse()
            if value == "players":
                res = self.board.view_players()
            elif value == 'map':
                # recebia self.player
                res = self.board.view_global_weights()
            elif value == 'obstacles':
                # recebia self.player
                res = self.board.view_obstacles()
            elif value == 'targets':
                res = self.board.view_targets()

            elif value == 'maxcoord':
                res = self.board.get_max_coord()
                # print('MaxCoordinates:', res)
            # elif value == 'north':
            #     front = self.board.get_place_direction(self.player, 'north')
            #     res = self.board.view_object(*front)
            # elif value == 'south':
            #     front = self.board.get_place_direction(self.player, 'south')
            #     res = self.board.view_object(*front)
            # elif value == 'east':
            #     front = self.board.get_place_direction(self.player, 'east')
            #     res = self.board.view_object(*front)
            # elif value == 'west':
            #     front = self.board.get_place_direction(self.player, 'west')
            #     res = self.board.view_object(*front)
            else:
                pass

        # Mark and unmark
        elif cmd_type == "mark":
            value = value_type
            try:
                self.board.mark(*[int(i) for i in value.split("_")[0].split(",")], value.split("_")[1])
                res = True
            except:
                res = ""

        elif cmd_type == "unmark":
            value = value_type
            try:
                self.board.unmark(*[int(i) for i in value.split(",")])
                res = True
            except:
                res = ""
        return res

    def connect(self):
        return self.server_socket.s_connect()

    def loop(self):
        # Test
        print("Starting the loop")
        self.server_socket.settimeout_conn(0.5)
        while True:
            try:
                data = self.server_socket.s_receive_msg()
                cmd_type, value_type = "", ""
                if len(data) >= 2:
                    cmd_type, value_type = data
                #Test
                #print("Received cmd_type=",cmd_type," value=",value)
                res = self.execute(cmd_type, value_type)
                if res != '':
                    return_data = str.encode(str(res))
                else:
                    return_data = str.encode(
                        "\ncommand <nr_op>,  <nr> = number of the agent, <op> = north; south; east; west"
                        + "\ninfo <op> <op> = map; targets; players; obstacles; maxcoord"
                        + "\nmark x,y_color" +  "\nunmark = x,y")
                self.server_socket.s_send_msg(return_data)
                self.root.update()
            except socket.timeout:
                # Test
                # print("Timeout!")
                self.root.update()


def main():
    with open("config_big.json") as config_file:
        config = json.load(config_file)
    # Host and Port
    if len(sys.argv) == 3:
        host, port = sys.argv[1], int(sys.argv[2])
    else:
        host = config["host"]
        port = config["port"]

    # Initialize the server
    server = Server(host, port, config)
    server.connect()
    # Loop ...
    server.loop()


if __name__ == "__main__":
    main()
