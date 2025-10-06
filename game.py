import data.cities

class PandemicGame:
    cities = data.cities.build_city_graph()

    def __init__(self, seed=None):
        self.seed = seed
        self.state = {"phase": "lobby"}

    def validate_action(self, player, action):
        # TODO: проверить корректность действия
        return True

    def apply_action(self, action):
        # TODO: модифицировать self.state
        pass