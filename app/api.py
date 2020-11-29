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

def redis_increment():
	r = RedisD.Redis(host='redis',port='6379',db=0)
	try:
		if r.ping():
			r.incr('compteur')
			return int(r.get('compteur'))
	except:
		return 0

@app.route('/')
def home():
		# compteur de visite :
		counter_redis = redis_increment()

		# valeurs retournees pour la vue
		data = { "counter_redis" : counter_redis }

		return render_template("home.html", data=data)

@app.route('/login')
def login():
		# compteur de visite :
		counter_redis = redis_increment()

		# valeurs retournees pour la vue
		data = { "counter_redis" : counter_redis }
		return render_template("login.html", data=data)

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
		conn_neo = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "admin"))
		return {
		'neo4j': ['connexion:', 'OK']
		}
	except:
		return {
			'neo4j': ['fail']
		}

def create_or_get_user(tx, name):
    result = tx.run("MERGE (n:User {name: $name})"
           "RETURN n.name AS name", name=name)
    names = []
    for record in result:
        names.append(record["name"])
    return names


@app.route('/neo4j/getUser/<name>')
def neo4jGetUser(name):
	conn_neo = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "admin"))
	return {'userName' : [conn_neo.session().write_transaction(create_or_get_user, name)]}
			

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