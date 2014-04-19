# The game world is a represention of the world in which the players interact.
#
class Chatroom(object):
    def __init__(self):
        self.logged_in = {}
        self.not_logged_in = []

    def add(self, key):
        self.not_logged_in.append(key)
        self.manager.send_message([key], "Welcome! Type <code>connect username</code> to log in!")

    def do(self, key, command):
        if key in self.logged_in:
            me = self.logged_in[key]
            self.manager.send_message([key],"You say '%s'"%command)
            others = [p for p in self.logged_in.keys() if p != key]
            self.manager.send_message(others, "%s says '%s'"%(me.name,command) )
        elif key in self.not_logged_in:
            params = command.split()
            if params[0] == "connect" and len(params) > 1:
                name = params[1]
                self.not_logged_in.remove(key)
                self.logged_in[key] = Player(name, key, manager)
                self.manager.send_message([key], "Welcome, %s!"%name)



# Players represent logged-in users in the world. Players can move around the
# world freely and queue actions to be performed.
class Player(object):
    def __init__(self, name, key, manager):
        self.name = name
        self.manager = manager
        self.key = key

    def send(self, message):
        self.manager.send_message([key], message)

# Start the mud.
import httpmud
httpmud.start(Chatroom())
