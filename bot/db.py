from config import config
from pymongo import MongoClient

client = MongoClient(config["db"])

ctfdb = client["ctftime"]  # Create ctftime database
ctfs = ctfdb["ctfs"]  # Create ctfs collection
challdb = ctfdb["challs"]  # Create challs collection
teamdb = client["ctfteams"]  # Create ctf teams database
serverdb = client["serverinfo"]
