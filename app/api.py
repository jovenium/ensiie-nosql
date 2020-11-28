#################################
#~~~~~~ App ENSIIE- NOSQL ~~~~~~# 
#################################

# Import framework
from flask import Flask,render_template	
#from flask_restful import Resource, Api 
import redis as RedisD
import psycopg2
from neo4j import GraphDatabase
from pymongo import MongoClient

# initialisation de l'application
app = Flask(__name__)
#api = Api(app)

@app.route('/')
def home():
		return render_template("home.html")

@app.route('/login')
def login():
		return render_template("login.html")

@app.route('/redis')
def redis():
	r = RedisD.Redis(host='redis',port='6379',db=0)
	try:
		if r.ping():
			r.incr('compteur')
			compteur = r.get('compteur')	
			return {
			'redis': ['compteur:', str(compteur)]
			}
	except:
		return {
			'redis': ['fail']
		}
			
@app.route('/psql')
def postgres():
	try:
		conn = psycopg2.connect(
			host="psql",    #nom du service compose
			database="postgres",
			user="postgres",
			password="postgres",
			port='5432')
		
		return {
		'psql': ['connexion:', 'OK']
		}
	except:
		return {
			'psql': ['fail']
		}
			
@app.route('/neo4j')
def neo4j():
	try:
		conn_neo = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "neo4j"))
		
		return {
		'neo4j': ['connexion:', 'OK']
		}
	except:
		return {
			'neo4j': ['fail']
		}
			
@app.route('/mongo')
def mongo():
	try:
		client = MongoClient('mongodb://mongo:mongo@mongo')
		
		return {
		'mongo': ['connexion:', client.db_name.command('ping')]
		}
	except:
		return {
			'mongo': ['fail']
		}

# Lancement de l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)