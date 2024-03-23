import json

class JsonTool:
    def __init__(self, path):
        self.path = path
        
    def get_data(self):
        # Open the JSON file
        with open(self.path, 'r') as f:
            # Load the JSON data
            data = json.load(f)
        return data