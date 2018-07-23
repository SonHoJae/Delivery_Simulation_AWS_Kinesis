import socket
import sys
import traceback
import json
import ast
from collections import OrderedDict
from threading import Thread

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
            try:
                client_input = ast.literal_eval(client_input)
                # order_created
                if  9 == len(client_input):
                    insertToRankingMemory(client_input)
                    get_created_total_price(client_input)
                    connection.sendall("-".encode("utf8"))
                # order_assigned
                elif 3 == len(client_input):
                    print(client_input)
                # order_completed
                else:
                    get_completed_total_price(client_input)
                    print(client_input)
            except SyntaxError:
                print('syntax error')
                pass

def receive_input(connection, max_buffer_size):
    client_input = connection.recv(max_buffer_size)
    client_input_size = sys.getsizeof(client_input)

    if client_input_size > max_buffer_size:
        print("The input size is greater than expected {}".format(client_input_size))

    result = client_input.decode("utf8").rstrip()  # decode and strip end of line
    return result

# Rank from ship_from_region for 10 minutes and previous data go to database
# For tackling streaming data, all the data should be processed on memory
# MongoDB query runs on memory, but memory architecture is ~~
def ranking_sort(updated_order):
    global top_10_region
    global top_10_region_key
    global lowest_rank

    new_key, new_value = None, None
    for k,v in updated_order.items():
        new_key, new_value = k, v
    top_10_region[k] = v
    a = sorted(list(top_10_region.items()), key=lambda x: x[1], reverse=True)
    # print(a[:10])
    #TODO : IMPORVE SORTING ALGORITHM
    #
    # if len(top_10_region) == 0:
    #     top_10_region[new_key] = new_value
    #     top_10_region_key.append(new_key)
    # else:
    #     if new_key in top_10_region:
    #         top_10_region[new_key] = new_value
    #         top_10_region_key.append(new_key)
    #     else:
    #         for key, value in top_10_region.items():
    #             if value < new_value:

def insertToRankingMemory(data):
    global top_10_region

    region = str(data['ship_from_region_x'])+','+str(data['ship_from_region_y'])
    if region in top_10_region:
        order_created[region] += 1
    else:
        order_created[region] = 1
    ranking_sort({region: order_created[region]})

def get_created_total_price(data):
    global total_created_price
    price = data['price']
    total_created_price += price
    print("created price " + str(total_created_price))

def get_completed_total_price():
    global total_completed_price
    cursor = delivery_collection.find({'status':2})
    for document in list(cursor):
        total_completed_price += document['price']
    print("completed price " + str(total_completed_price))


delivery_collection = database_collection()
delivery_collection.drop()
client_socket = None
order_created = {}
top_10_region = OrderedDict()
total_created_price = 0
total_completed_price = 0

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