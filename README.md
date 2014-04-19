HTTPMud
=======
HTTPMud is a new kind of MUD (Multi-User Dungeon) that is built around HTTP GET and POST requests instead of the raw sockets of old-fashioned Telnet MUDs. HTTPMud is built from the power of JQuery and CherryPy.

How does it work?
-----------------
All you have to do is import the httpmud library and create an object to represent your MUD's world. Your world only needs two methods to interact with the server: a ```do``` method that takes a single command from the client, and an ```add``` method that indicates when a new client connects to the server.

The manager keeps a queue of all of the commands that should be processed. In order to avoid keeping the clients waiting, the server should batch its commands by putting commands in the queue instead of running long loops. All user commands are directly injected to the queue by the manager as long as they are connected to a valid session.
