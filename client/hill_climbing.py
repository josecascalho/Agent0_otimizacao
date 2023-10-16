import client
import ast
MAX = 1000
# --------------------------------------------
# Estratégia adoptada para este trepa colinas
# --------------------------------------------
# Escolhe um jogador
# Identifica todas as jogadas possíveis (vizinhanças)
# Considera para cada uma das jogadas um novo estado
# -- calcula o valor de heurística para cada um desses estados
# -- escolhe a melhor jogada
# Repete para os outros jogadores
# Termina ao fim de x iterações ou quando não descobre uma solução melhor
# ---------------------------------------------

class Agent:
    def __init__(self):
        self.c = client.Client('127.0.0.1', 50001)
        self.res = self.c.connect()
        self.targets = [] # houses' locations
        self.state = []
        self.neighbour_states = []
        self.weight_map =[]
        self.weight_dict = {}
        self.max_coord = (0,0)
        self.obstacles = []

    def get_targets(self):
        """
        Get targets (houses) positions
        """
        msg = self.c.execute("info", "targets")
        targets = ast.literal_eval(msg)
        # test
        # print('Targets list:', targets)
        return targets

    def set_state(self):
        """
        Set the state getting hospital places
        """
        msg = self.c.execute("info", "players")
        players = ast.literal_eval(msg)
        self.state = players
        # Test
        print('Initial state:', self.state)



    def get_weight_map(self):
        """
        Get weights
        """
        msg = self.c.execute("info", "map")
        w_map = ast.literal_eval(msg)
        # test
        # print('Received map of weights:', w_map)
        return w_map

    def get_weight_dict(self):
        """Transform the weights into a dictionary"""
        msg = self.c.execute("info", "map")
        w_map = ast.literal_eval(msg)

        w_dict = {}
        for elem in w_map:
            w_dict[elem[0]]=elem[1]
        # Test
        # print(w_dict)
        return w_dict

    def get_max_coord(self):
        msg = self.c.execute("info","maxcoord")
        max_coord =ast.literal_eval(msg)
        # Test
        # print('Received maxcoord', max_coord)
        return max_coord

    def get_obstacles(self):
        msg = self.c.execute("info","obstacles")
        obst =ast.literal_eval(msg)
        # Test
        # print('Received map of obstacles:', obst)
        return obst

    def step(self,pos,action):
        """Add new position after an action, using north, east, west or south"""
        if action == "east":
            if pos[0] + 1 < self.max_coord[0]:
                new_pos = (pos[0] + 1, pos[1])
            else:
                new_pos =(0,pos[1])

        elif action == "west":
            if pos[0] - 1 >= 0:
                new_pos = (pos[0] - 1, pos[1])
            else:
                new_pos = (self.max_coord[0] - 1, pos[1])

        elif action == "south":
            if pos[1] + 1 < self.max_coord[1]:
                new_pos = (pos[0], pos[1] + 1 )
            else:
                new_pos = (pos[0], 0)

        elif action == "north":
            if pos[1] - 1 >= 0:
                new_pos = (pos[0], pos[1] - 1)
            else:
                new_pos = (pos[0], self.max_coord[1] - 1 )
        return new_pos

    def mark(self, pos:tuple, colour:str):
        mark_ground = str(pos[0])+","+str(pos[1])+"_"+colour
        msg = self.c.execute("mark",mark_ground)
        obst =ast.literal_eval(msg)

    def unmark(self,pos:tuple):
        unmark_ground = str(pos[0])+","+str(pos[1])
        msg = self.c.execute("unmark",unmark_ground)
        obst =ast.literal_eval(msg)

    def get_heuristic(self, state: tuple, target:tuple) -> int:
        '''This heuristic uses the Manhattan distance.
        calculating the differences between x and y coordinates
        state: coordinates of the state
        target: coordinates of the target
        output: Manhattan distance (int)
        '''
        diff_in_x = target[0] - state[0]
        if diff_in_x < 0:
            diff_in_x = (-1) * diff_in_x
        diff_in_y = target[1] - state[1]
        if diff_in_y < 0:
            diff_in_y = (-1) * diff_in_y

        return diff_in_x + diff_in_y

    def get_closer_player(self,target:tuple,state:list)->tuple:
        """
        For the target, discover which element in state is closer
        and return it
        """
        hf = MAX
        closer = None
        for elem in state:
            h = self.get_heuristic(elem[1],target)
            if h < hf:
                hf =  h
                closer = elem
        return (hf,closer)


    def sum_up_heuristics(self,state: list)->int:
        """
        For the state, find the heuristic value: Sum of all distances
        from target to closest player
        """
        h_t = 0
        for target in self.targets:
            h, player = self.get_closer_player(target,state)
            h_t += h
        # Test
        print("For state ",state," the total heuristics is",h_t)
        return h_t

    def state_has_obstacle(self, state:tuple):
        obstacle = False
        for obst in self.obstacles:
            if state == obst:
                obstacle = True
                break
        # Test
        #print("State ",state," is in an obstacle? ", obstacle)
        return obstacle

    def state_has_target(self, elem:tuple):
        """
        Test if there is a target in the elem position
        """
        t = False
        for target in self.targets:
            if elem == target:
                t = True
                break
        # Test
        #print("State ",state," has a target? ", player)
        return t


    def state_has_player(self, elem:tuple):
        """
        Test if in state state there is a player.
        State has the structure (x,y).
        Player list has the following structure [(n0,(x0,y0)),(n1,(x1,x2))...]
        where n is the number of the player and (x,y) are the coordinates. etc
        """
        p = False
        for pl in self.state:
            if elem == pl[1]:
                p = True
                break
        # Test
        #print("State ",state," has a player? ", player)
        return p


    def neigbours(self, player: tuple) -> list:
        """
        For a player find all neigbours where it can move.
        It includes the initial position ("none")
        """
        neighbours = [["none",player[1]]]
        for act in ["north","east","south","west"]:
            new_pos = self.step(player[1],act)
            if not self.state_has_obstacle(new_pos) and not self.state_has_player(new_pos) and not self.state_has_target(new_pos):
                neighbours.append([act,new_pos])
        return neighbours

    def get_new_state(self,player: tuple,neighbour:tuple) -> list:
        """
        This method removes player from self.state and adds to
        a new state the new position of player
        It assumes player is (n,(x,y)) with n the number of the player
        and neighbour is (d,(x,y)) with d corresponding to direction
        """
        new_state = []
        # Find the player
        print("Player:",player)
        print("Neighbour",neighbour)
        for elem in self.state:
            if elem[0] == player[0]:
                new_state.append((player[0],neighbour[1]))
            else:
                new_state.append(elem)
        return new_state

    def select_action(self, player: tuple) -> str:
        """
        Select action to execute (including "none") depending on
        the calculated heuristic value for each one of the actions
        """
        # Get all neighbours of player ...
        neighbours = self.neigbours(player)
        # Test
        #print("The neighbours of player ",player[0] ,"are:",neighbours)
        # For each neighbour, get heuristic value ...
        final_heuristic = MAX
        action ="None"
        for neighbour in neighbours:
            new_state = self.get_new_state(player,neighbour)
            # Test
            #print("New state for action ",neighbour[0],":",new_state)
            # Get the heuristic of this new state:
            value = self.sum_up_heuristics(new_state)
            if value < final_heuristic:
                final_heuristic = value
                action = neighbour[0]
        # Test (Results of possible actions of one player)
        #print("The final heuristic value is for this player ", final_heuristic)
        #print("and the action for that target is ",action)
        return action

    def run(self):
        # Get the targets
        self.targets = self.get_targets()
        # Test
        print("Targets:",self.targets)
        # Get information of the weights for each step in the world ...
        self.weight_dict = self.get_weight_dict()
        # Test
        #print("weights dict:",self.weight_dict)
        self.obstacles = self.get_obstacles()
        # Test
        #print("obstacles:", self.obstacles)
        # Get max coordinates
        self.max_coord = self.get_max_coord()
        # Start thinking
        end = False
        # Testing just one case: selecting one of the players (hospital)
        # Set initial state
        # self.set_state()
        # print("Selecting the first player from the state:", self.state[0])
        # direction = self.select_action(self.state[0])
        # if direction != "none":
        #     value = str(self.state[1][0])+"_"+ direction
        #     # Test
        #     print("Message sent: command ",value)
        #     self.c.execute("command",value)
        # else:
        #     print("No action!")
        #
        print("Carregue em tecla para começar")
        # General case
        input()
        self.set_state()
        # Number of players:
        size = len(self.state)
        # Cycle expanding nodes following the sequence in frontier nodes.
        i = 0
        cycle = 0
        stopped = []
        while end == False and cycle <= 200:
            print("Cycle", cycle)
            print("Selecting the player ",i%size," from the state:", self.state[i%size])
            direction = self.select_action(self.state[i%size])
            if direction != "none":
                value = str(self.state[i%size][0])+"_"+ direction
                # Test
                #print("Message sent: command ",value)
                self.c.execute("command",value)
            else:
                # Test
                #print("Already stopped:",stopped)
                if not i%size in stopped:
                    print("No action for agent ",i%size,"!")
                    stopped.append(i%size)
            if len(stopped) == size:
                end = True
            if i%size == 0:
                cycle += 1
            #input()
            # New state...
            self.set_state()
            i += 1
        print("Final step! Press to exit.")
        input()

# Starting the program...
def main():
    agent = Agent()
    agent.run()

main()