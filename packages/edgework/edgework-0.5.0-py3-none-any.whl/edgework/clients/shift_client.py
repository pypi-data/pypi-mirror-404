from httpx import Client


class ShiftClient:
    def __init__(self, client: Client):
        self.client = client

    def get_shifts(self, game_id):
        """

        :param game_id:
        :return:
        """
