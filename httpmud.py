import cherrypy
import threading
import time
import json

import gameworld

# The manager keeps track of the messages that should be sent to each client and
# the commands the clients send to the server. Clients are pruned when they idle
# for too long. The world that's provided needs an 'add' and a 'do' method, but
# for the most part, can do whatever it wants.
class Manager(object):
    def __init__(self, world):
        self.world = world
        self.queue = []
        self.messages = {}
        self.msg_id = 1
        self.time_limit = 1.0
        self.world.manager = self

    # Register a new connection with key. This creates a local copy of the
    # key for sending messages and passes the key to the world.
    def register(self, key):
        self.messages[key] = []
        self.world.add(key)

    # Queue up a command from either the system or
    def enqueue(self, command, key=None):
        self.queue.append((key, command))

    # Starts running commands in the queue for a limited amount of time.
    def tick(self):
        elapsed = 0.0
        start = time.time()
        if len(self.queue) > 0 and (time.time() - start) < self.time_limit:
            key, command = self.queue.pop(0)
            self.world.do(key, command)

    # Send a message to each key in keys. Each message has an id number and
    # a string. The id allows the client to keep track of which messages it
    # has seen.
    def send_message(self, keys, message):
        if keys=="all":
            keys = self.messages.keys()
        for k in keys:
            if k in self.messages:
                self.messages[k].append((self.msg_id,message))
                self.messages[k] = self.messages[k][:100]
        self.msg_id += 1

    # Get all of the messages for the user with 'key' since since. The client
    # is responsible for knowing what to ask for.
    def get_messages(self, key, since):
        if key in self.messages:
            report = [x for x in self.messages[key] if x[0] > since]
            return report
        return []


# The interface is essentially the thin client that the player uses to interact
# with the server.
lock = threading.Lock()
class Interface(object):
    def __init__(self, manager):
        self.manager = manager
        self.active = []
        self.count = 1

    exposed = True

    # The GET method returns the static index that contains the thin client.
    def GET(self):
        me = cherrypy.session.id, cherrypy.session.get("user",None)

        # If the client isn't attached to a session yet, attach them to a
        # session.
        if me[1] is None:
            lock.acquire()
            me = cherrypy.session.id, self.count
            cherrypy.session["user"] = self.count
            self.active.append(me)
            self.count += 1
            self.manager.register(me)
            lock.release()

        # Return the thin client - this is a simple HTML page with an input
        # buffer and a javascript endless loop that sends Ajax requests asking
        # for feedback.
        return """<html>
                  <h1>HTTPMud</h1>
                  <body>
                  <div id="buffer"></div>
                  <p>
                  <input type="text" name="command" id="cmd"></input>
                  </p>
                  </body>
                  <script src="//ajax.googleapis.com/ajax/libs/jquery/2.1.0/jquery.min.js"></script>
                  <script>
                    var last = 0;
                    //send the message
                    function docommand(command) {
                    	$.ajax({
                    		type: "POST",
                    		url: "",
                    		data: {'command':command, 'since':last},
                    		dataType: "json",
                    		success: function(data){
                                for (var i=0; i<data["messages"].length; i++)
                    			{
                                    $('#buffer').append("<p>"+data["messages"][i][1]+"</p>");
                                    last = data["messages"][i][0];
                                }
                    		}
                    	});
                    }

                    $('#cmd').keydown(function (e){
                        if(e.keyCode == 13){
                            docommand($('#cmd').val());
                            $('#cmd').val("");
                        }
                    })

                    setInterval(function(){docommand("")},5000);
                  </script>
                  </html>
                  """

    # POSTs occur either on a timer or when the player sends a message to the
    # server. POSTs keep the game server ticking and and allow the player to
    # send their commands. Commands are enqueued and processed during the tick
    # phase.
    def POST(self, command="", since=""):
        me = cherrypy.session.id, cherrypy.session.get("user",None)
        if me not in self.active:
            raise cherrypy.HTTPError(403)

        # We can only advance the world when we get a signal from a client. If
        # clients stop signaling, then we stop ticking.
        data = ""
        lock.acquire()
        if command:
            self.manager.enqueue(command, me)
        self.manager.tick()
        if since and since.isdigit():
            report = self.manager.get_messages(me, int(since))
            if report:
                data = json.dumps({"messages":report})
        lock.release()

        return data


# Pass your world model into this method to begin your game.
def start(world):
    conf = { "global":
             {
                "server.socket_host": '0.0.0.0',
                "tools.sessions.on": True,
                "tools.sessions.timeout": 60
             },
             "/":
             {
                "request.dispatch": cherrypy.dispatch.MethodDispatcher()
             }
           }
    man = Manager(world)
    cherrypy.quickstart(Interface(man),"/",conf)
