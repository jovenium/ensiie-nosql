# Product Service

# Import framework
from flask import Flask
from flask_restful import Resource, Api
import redis
import psycopg2
from neo4j import GraphDatabase
from pymongo import MongoClient

# Instantiate the app
app = Flask(__name__)
api = Api(app)


class Redis(Resource):
	def get(self):
		r = redis.Redis(host='redis',port='6379',db=0)
		try:
			if r.ping():
				r.incr('compteur')
				compteur = r.get('compteur')	
				return {
				'redis': ['compteur:', str(compteur)]
				}
		except:
			return {
				'fails': ['fails', 'fails', 'fails', 'fails']
			}
			
			
class Postgres(Resource):
	def get(self):
		try:
			conn = psycopg2.connect(
				host="psql",    #nom du service compose
				database="postgres",
				user="postgres",
				password="postgres",
				port='5432')
			
			return {
			'psql': ['ping:', 'pong']
			}
		except:
			return {
				'psql': ['fail']
			}
			
class Neo4j(Resource):
	def get(self):
		try:
			conn_neo = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "neo4j"))
			
			return {
			'neo': ['4j', 'OK']
			}
		except:
			return {
				'neo': ['fail']
			}
			
class Mongo(Resource):
	def get(self):
		try:
			client = MongoClient('mongodb://mongo:mongo@mongo')
			
			return {
			'mongo': ['ognom']
			}
		except:
			return {
				'mongo': ['nop']
			}

# Create routes
api.add_resource(Redis, '/')
api.add_resource(Postgres, '/psql')
api.add_resource(Neo4j, '/neo4j')
api.add_resource(Mongo, '/mongo')

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)