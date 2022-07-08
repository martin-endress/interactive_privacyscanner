// Init ELM
var app = Elm.Main.init({ node: document.getElementById("container") });

// Instantiate client, using an HTTP tunnel for communications.
var client = new Guacamole.Client(
    new Guacamole.HTTPTunnel("/guac/guacamole-backend-1.0/tunnel")
);

// Add client to display div
var displayEl = document.getElementById("display");
displayEl.appendChild(client.getDisplay().getElement());

// Send port messages
function sendGuacamoleErrorMsg(msg) {
    msg_json = { "GuacamoleMsg": msg }
    app.ports.messageReceiver.send(msg_json)
}

client.onstatechange = function (state) {
    //const state_msg = 'new state=' + state;
    //sendGuacamoleErrorMsg(state_msg);
}

// Send errors to Elm port
client.onerror = function (error) {
    const error_msg = 'guac error (status=' + error.code.toString() + ') - ' + error.message;
    sendGuacamoleErrorMsg(error_msg);
};

// Disconnect on close
window.onunload = function () {
    // TODO wire this up with ELM
    client.disconnect();
    socket.close();
}

// Mouse and keyboard events on focus / unfocus
const mouse = new Guacamole.Mouse(client.getDisplay().getElement());
const keyboard = new Guacamole.Keyboard(document);

// Focus guacamole element including key and mouse events
function focusGuacamole() {
    document.activeElement.blur();
    // Mouse
    mouse.onmousedown =
        mouse.onmouseup =
        mouse.onmousemove = function (mouseState) {
            client.sendMouseState(mouseState);
        };

    keyboard.onkeydown = function (keysym) {
        client.sendKeyEvent(1, keysym);
    };

    keyboard.onkeyup = function (keysym) {
        client.sendKeyEvent(0, keysym);
    };
}

// Remove focus from guacamole element
function unfocusGuacamole() {
    document.activeElement.blur();
    mouse.onmousedown =
        mouse.onmouseup =
        mouse.onmousemove = null;
    keyboard.onkeyup =
        keyboard.onkeydown = null;
}

// ports
app.ports.setGuacamoleFocus.subscribe(function (focus) {
    if (focus) {
        focusGuacamole();
    } else {
        unfocusGuacamole();
    }
})

// connect to guacamole
app.ports.connectTunnel.subscribe(function (connection) {
    connectGuacamole(connection);
});

function connectGuacamole(connection) {
    param = "port=" + connection.vncPort.toString()
    client.connect(param);
}

// Init Websocket
var socket;

function init_ws() {
    socket = new WebSocket('wss://scanner.psi.live/ws/add_socket');
    // Event listeners
    socket.onopen = function (event) {
        app.ports.messageReceiver.send({ "Log": "Web Socket opened."});
    };
    socket.onclose = function (event) {
        app.ports.messageReceiver.send({ "SocketError": "Web Socket closed."});
    };
    socket.onmessage = function (event) {
        try {
            app.ports.messageReceiver.send(JSON.parse(event.data));
        } catch (SyntaxError) {
            msg_json = { "SocketError": "Syntax error in socket message from server." };
            app.ports.messageReceiver.send(msg_json);
        }
    };
    socket.onerror = function (event) {
        msg_json = { "SocketError": "Web socket.error, this should never happen :( . Check if Backend is up." };
        app.ports.messageReceiver.send(msg_json);
    };
}

window.onload = init_ws;

// disconnect from guacamole
app.ports.disconnectTunnel.subscribe(function () {
    client.disconnect();
});
