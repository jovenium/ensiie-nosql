#################################
#~~~~~~ App ENSIIE- NOSQL ~~~~~~# 
#################################

# Import framework
from flask import Flask,render_template, request, redirect, url_for, session
import logging
import os
import datetime
#from flask_restful import Resource, Api 
import redis as RedisD
import psycopg2
import uuid
from neo4j import GraphDatabase
from pymongo import MongoClient

# initialisation de l'application
app = Flask(__name__)
databases= {1: 'neo4j', 2: 'mongodb', 3: 'postgres'}
conn_neo = None
conn_red = RedisD.Redis(host='redis',port='6379',db=0)
conn_mon = None
conn_psq = psycopg2.connect(host="psql",database="postgres",user="postgres",password="postgres",port='5432')

def get_neo4J_connexion():
	global conn_neo
	if conn_neo is None:
		conn_neo = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "admin"))
	return conn_neo

def get_mongodb_connexion():
	global conn_mon
	if conn_mon is None:
		conn_mon = MongoClient('mongodb://mongo:mongo@mongo')
	return conn_mon

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
	if session.get('logged_in') :
		return redirect(url_for('todo',name = session.get('todo')))
	return redirect(url_for('login'))

@app.route('/<name>')
def todo(name):
		if not session.get('logged_in') :
			return redirect(url_for('login'))
		# compteur de visite :
		counter_redis = redis_increment()
		# post-its 
		neo4j_postits = get_neo4J_connexion().session().write_transaction(get_post_it, name)
		mongodb_postits = get_post_it_mongo(name)
		# valeurs retournees pour la vue
		data = { "counter_redis" : counter_redis , "postits" : [neo4j_postits,mongodb_postits] }
		return render_template("home.html", data=data)

@app.route('/login',methods = ['POST', 'GET'])
def login():
		if request.method == 'POST':
			login = request.form['name']
			# check si le login est bien dans les 3 bases puis ajout dans les 3 bases
			neo4jGetUser(login) # neo4j
			mongodbGetUser(login) #TODO mongo
			#TODO psql
			session['logged_in'] = True
			session['todo'] = login
			return redirect(url_for('todo',name = login))
		else:
			if session.get('logged_in') :
				return redirect(url_for('todo',name = session.get('todo')))
			# compteur de visite :
			counter_redis = redis_increment()
			# valeurs retournees pour la vue
			data = { "counter_redis" : counter_redis }
			return render_template("login.html", data=data)

@app.route('/deconnection', methods = ['POST'])
def deconnection():
	session['logged_in'] = False
	session['todo'] = ""
	return redirect(url_for('login'))

@app.route('/createPostIt', methods=['POST'])
def createpostit():
	if not session.get('logged_in') :
		return redirect(url_for('login'))
	user = session.get('todo')
	title = request.form["name"]
	description = request.form["description"]
	todo_date = request.form["event_date"]
	todo_date = todo_date[6::] + todo_date[2:5] + "-" + todo_date[0:2]
	app.logger.info(todo_date)
	importance = request.form["importance"]
	database_num = request.form["database"]

	if databases[int(database_num)] == databases[1] :
		get_neo4J_connexion().session().write_transaction(create_post_it, user, title, todo_date, description, importance)
		app.logger.info("add post-it neo4j")
	elif databases[int(database_num)] == databases[2] :
		#do some mongo
		create_post_it_mongo(user, title, todo_date, description, importance)
		app.logger.info("add post-it mongo")
	else :
		#do some psql
		app.logger.info("NON add post-it psql")

	return redirect(url_for('todo',name = user))

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
		GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "admin"))
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


@app.route('/neo4j/getUser/<name>', methods=['GET'])
def neo4jGetUser(name):
	return {'userName' : [get_neo4J_connexion().session().write_transaction(create_or_get_user, name)]}

def create_post_it_mongo(user, title, todo_date, description, importance):
	conn_mon=get_mongodb_connexion()
	db=conn_mon.ToutDoux
	now = datetime.datetime.now()
	nowDate = str(now.year) + "-" + str(now.month) + "-" + str(now.day)
	app.logger.info(nowDate)
	postit={"name": title ,"user": user, "creationDate": nowDate, "toDoDate": todo_date,'isDone':False, "description": description, "importance": importance}
	app.logger.info(postit)
	db.PostIt.insert_one(postit)	

def get_post_it_mongo(user):
	conn_mon=get_mongodb_connexion()
	db=conn_mon.ToutDoux
	postits = list(db.PostIt.find({'user':user}))
	app.logger.info(postits)
	for postit in postits :
		postit['dataBase']='mongodb'
	return postits

def create_post_it(tx, userName, postItName, toDoDate, description, importance):
    tx.run("Match(u:User {name : $userName})"
        "CREATE(p:PostIt {uuid : apoc.create.uuid(),"
			"name: $postItName,"
            "creationDate : date(),"
            "toDoDate : date($toDoDate),"
            "isDone : false,"
            "description : $description,"
			"importance : $importance})"
        "create (u)-[:haveToDo]->(p)", userName=userName, postItName=postItName, toDoDate=toDoDate, description=description, importance=importance)

@app.route('/neo4j/createPostIt', methods=['POST'])
def neo4j_createpostit():
    try:
        form = request.form
        get_neo4J_connexion().session().write_transaction(create_post_it, form["userName"], form["postItName"], form["toDoDate"], form["description"])
        return {
		    'addPostIt': 'succes'
		    }
    except:
        return {
			'addPostIt': 'fail'
		}	

def get_post_it(tx, name):
    result = tx.run("MATCH (:User { name: $name })-->(p:PostIt) RETURN p AS postIt", name=name)
    postIts = []
    for record in result:
        properties = {}
        for key in record["postIt"].keys():
            print(key)
            if(key == "toDoDate" or key == "creationDate"):
                date = record["postIt"][key]
                properties[key] = date.iso_format()
            else:
                properties[key] = record["postIt"][key]
        properties["dataBase"] = "neo4j"
        postIts.append(properties)
    print(postIts)
    return postIts


@app.route('/neo4j/getPostIt/<name>', methods=['GET'])
def neo4j_get_post_it_of(name):
    try:
        return {
		    'getPostIt': get_neo4J_connexion().session().write_transaction(get_post_it, name)
		    }
    except:
        return {
			'getPostIt': 'fail'
		}

def set_done(tx, uuid):
	tx.run("match (p:PostIt{uuid: $uuid}) set p.isDone = true", uuid=uuid)


@app.route('/neo4j/setDone/<uuid>')
def neo4j_set_done(uuid):
	try:
		get_neo4J_connexion().session().write_transaction(set_done, uuid)
		return redirect(url_for('home'))
	except:
		return redirect(url_for('home'))

def remove_post_it(tx, uuid):
	tx.run("match (p:PostIt{uuid: $uuid}) detach delete p", uuid=uuid)


@app.route('/neo4j/removePostIt/<uuid>')
def neo4j_remove_post_it(uuid):
	try:
		get_neo4J_connexion().session().write_transaction(remove_post_it, uuid)
		return redirect(url_for('home'))
	except:
		return redirect(url_for('home'))
 

def mongodbGetUser(name):
	conn_mon = get_mongodb_connexion()
	collection = conn_mon.ToutDoux 
	user = { "name" : name }
	collection.User.update(user,{ "$set" :user}, upsert=True)

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
	app.secret_key = os.urandom(12)
	app.run(host='0.0.0.0', port=80, debug=True)