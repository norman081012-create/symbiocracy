class SymbiocracyGame:
    def __init__(self):
        self.state = 'initial'
        self.players = []

    def add_player(self, player_name):
        self.players.append(player_name)

    def start_game(self):
        self.state = 'in_progress'
        print('Game has started with players:', self.players)

    def end_game(self):
        self.state = 'ended'
        print('Game has ended.')