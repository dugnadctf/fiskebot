from pymongo import MongoClient
from auth import *

mclient = MongoClient(conn)

# Create databases
ctfdb = mclient['ctftime'] 
teamdb = mclient['ctfteams'] 
serverdb = mclient['serverinfo']
chaldb = mclient['chals']

# Create collections
ctfs = ctfdb['ctfs']
