import socket
import sys
import traceback
import ast
from collections import defaultdict
from threading import Thread
import datetime
from pymongo import MongoClient

def database_collection():
    client = MongoClient()
    db = client.delivery_database
    delivery_collection = db.delivery_collection
    print(db.collection_names())
    return delivery_collection

def start_server():
    host = "127.0.0.1"
    port = 8888         # arbitrary non-privileged port

    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state, without waiting for its natural timeout to expire
    print("Socket created")

    try:
        soc.bind((host, port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()

    soc.listen(5)       # queue up to 5 requests
    print("Socket now listening")

    # infinite loop- do not reset for every requests
    while True:
        connection, address = soc.accept()
        ip, port = str(address[0]), str(address[1])
        print("Connected with " + ip + ":" + port)

        try:
            Thread(target=client_thread, args=(connection, ip, port)).start()
        except:
            print("Thread did not start.")
            traceback.print_exc()
    soc.close()

def receive_input(connection, max_buffer_size):
    client_input = connection.recv(max_buffer_size)
    client_input_size = sys.getsizeof(client_input)

    if client_input_size > max_buffer_size:
        print("The input size is greater than expected {}".format(client_input_size))

    result = client_input.decode("utf8").rstrip()  # decode and strip end of line
    return result

''' Receiving events from consumers through socket '''
def client_thread(connection, ip, port, max_buffer_size = 5120):
    is_active = True

    while is_active:
        client_input = receive_input(connection, max_buffer_size)

        if "--QUIT--" in client_input:
            print("Client is requesting to quit")
            connection.close()
            print("Connection " + ip + ":" + port + " closed")
            is_active = False
        else:
            client_input = ast.literal_eval(client_input)
            # order_created
            if  9 == len(client_input):
                order_created_and_get_rank(client_input)
                get_created_total_price(client_input)
                connection.sendall("-".encode("utf8"))
            # order_assigned
            elif 2 == len(client_input):
                get_avg_response_time()
            # order_completed
            else: # 1 == len(client_input)
                print_top10_ranking()
                get_completed_total_price()
                get_avg_completion_time()
                print("Total < Created > price -> $ "+ str(total_created_price) + '\n'
                      +"Total < Completed > price -> $ " + str(total_completed_price))



''' Problem 1 Functions '''
# Rank from ship_from_region for 10 minutes and previous< completed > price data go to database
# For tackling streaming data, all the data should be processed on memory
# I did just local variable for TOP 10 From regions

def print_top10_ranking():
    print('****************************** TOP 10 From regions ************************************')
    if len(dict_region_count) < 10:
        for idx, i in enumerate(range(len(dict_region_count), 0, -1)):
            if len(dict_region_count[i]) != 0:
                print('Top ' + str(idx + 1) + ' ' + str(dict_region_count[i]) + ' ' + str(i) + ' counted')
    else:
        for idx, i in enumerate(range(len(dict_region_count), len(dict_region_count) - 10, -1)):
            if len(dict_region_count[i]) != 0:
                print('Top ' + str(idx + 1) + ' ' + str(dict_region_count[i]) + ' ' + str(i) + ' counted')
    print('****************************************************************************************')

def order_created_and_get_rank(data):
    global dict_region_count

    region = str(data['ship_from_region_x'])+','+str(data['ship_from_region_y'])
    if region in order_created:
        order_created[region] += 1
        dict_region_count[int(order_created[region])].append(region)
        dict_region_count[int(order_created[region])-1].remove(region)
    else:
        order_created[region] = 1
        dict_region_count[int(order_created[region])].append(region)

''' Problem 2 Functions '''
def get_created_total_price(data):
    global total_created_price
    price = data['price']
    total_created_price += price

def get_completed_total_price():
    global total_completed_price
    cursor = delivery_collection.find({'status':2})
    total_completed_price = 0
    for document in list(cursor):
        total_completed_price += document['price']

''' Problem 3 Functions '''
def get_avg_completion_time():
    cursor = delivery_collection.find({"order_completed_time": {"$exists": True}})
    documents = list(cursor)
    total = 0
    count = len(documents)
    for document in documents:
        dt_complete_time = datetime.datetime.strptime(document['order_completed_time'],"%Y-%m-%d %H:%M:%S.%f")\
                           - datetime.datetime.strptime(document['order_created_time'],"%Y-%m-%d %H:%M:%S.%f")
        total += dt_complete_time.total_seconds()
    try:
        print('Average < Completion > time -> '+ str(total/count) + ' seconds')
    except ZeroDivisionError:
        print('No completion data')
    except Exception as e:
        print(e)

def get_avg_response_time():
    cursor = delivery_collection.find({"order_assigned_time": {"$exists": True}})
    documents = list(cursor)
    total = 0
    count = len(documents)
    for document in documents:
        dt_response_time = datetime.datetime.strptime(document['order_assigned_time'],"%Y-%m-%d %H:%M:%S.%f")\
                           - datetime.datetime.strptime(document['order_created_time'],"%Y-%m-%d %H:%M:%S.%f")
        total += dt_response_time.total_seconds()
    try:
        print('Average < Response > time -> ' + str(total / count) + ' seconds')
    except ZeroDivisionError:
        print('No response data')
    except Exception as e:
        print(e)

delivery_collection = database_collection()
delivery_collection.drop()
client_socket = None

order_created = {}
dict_region_count = defaultdict(list)
top_10_region = []
total_created_price = 0
total_completed_price = 0

# TODO 1. Optimize algorithm on memory (o)
# TODO 2. Reflect driver's current location (o)
# TODO 3. Consider pickup time constraint (o)
# TODO 4. Documentation (o)

if __name__ == "__main__":
    start_server()

# from flask import Flask, render_template, request
# import requests
# from bs4 import BeautifulSoup
# import random
# import socket
# import threading
#
# app = Flask(__name__)
# suggestions_list = []
# conn  = None
#
# def server_program():
#     global suggestions_list
#     global conn
#     print('1')
#     # get the hostname
#     host = socket.gethostname()
#     port = 5004  # initiate port no above 1024
#
#     server_socket = socket.socket()  # get instance
#     # look closely. The bind() function takes tuple as argument
#     server_socket.bind((host, port))  # bind host address and port together
#
#     # configure how many client the server can listen simultaneously
#     server_socket.listen(2)
#     conn, address = server_socket.accept()  # accept new connection
#     print("Connection from: " + str(address))
#     print(conn)
# server_program()
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
#
# @app.route('/suggestions')
# def suggestions():
#     global suggestions_list
#     global conn
#     data = conn.recv(512).decode()
#     suggestions_list.append(str(data)+'\n')
#     print("from connected user: " + str(data))
#     return render_template('suggestions.html', suggestions=suggestions_list)
#
#
# if __name__ == '__main__':
#     app.run(debug=True)