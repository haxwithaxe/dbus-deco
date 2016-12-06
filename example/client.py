#!/usr/bin/env python3

from pydbus import SessionBus

#get the session bus
bus = SessionBus()
#get the object
the_object = bus.get("com.example.service")

'''
#call the methods and print the results
reply = the_object.HelloWorld()
print('hello', reply)

reply = the_object.Echo("test 123")
print('echo', reply)
'''

def debug(*args, **kwargs):
    print('debug: onCount', *args, **kwargs)

the_object.PropertiesChanged.connect(print)
#the_object.onCount.connect()
print('debug: count', the_object.Count)
the_object.Count += 1
print('debug: incremented', the_object.Count)
#the_object.Count = the_object.Count
