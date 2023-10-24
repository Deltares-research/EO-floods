class FloodMap:
    def __init__(
        self,
        start_date: str,
        end_date: str,
        geometry: list,
        provider: list = None,
        dataset: list = None,
    ) -> None:
        _check_space_time_constraints(
            start_date=start_date, end_date=end_date, geometry=geometry
        )
        _determine_datasets(start_date=start_date, end_date=end_date, geometry=geometry)

    @property
    def info(self):
        pass

    def preview_date(self):
        pass

    def generate_flood_extents(self):
        pass


@staticmethod
def _determine_datasets(start_date: str, end_date: str, geometry: list):
    pass


@staticmethod
def _check_space_time_constraints(start_date: str, end_date: str, geometry: list):
    pass
