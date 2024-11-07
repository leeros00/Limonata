class DataLogger:
    def __init__(self):
        self.log = []

    
    def log(self, sensor_data: float) -> None:
        self.log.append(sensor_data)
