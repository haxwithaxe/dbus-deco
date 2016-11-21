from pydbus import SessionBus

#get the session bus
bus = SessionBus()
#get the object
the_object = bus.get("com.example.service")

#call the methods and print the results
reply = the_object.HelloWorld()
print(reply)

reply = the_object.Echo("test 123")
print(reply)

the_object.PropertiesChanged.connect(print)
print('count', the_object.Count)
the_object.Count += 1

the_object.Quit()
