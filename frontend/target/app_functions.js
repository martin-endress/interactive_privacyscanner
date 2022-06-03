// Init ELM
var app = Elm.Main.init({ node: document.getElementById("container") });

// Instantiate client, using an HTTP tunnel for communications.
var guac = new Guacamole.Client(
    new Guacamole.HTTPTunnel("http://scanner.psi.live/guac/guacamole-backend-1.0/tunnel")
);

// Add client to display div
var display = document.getElementById("display");
display.appendChild(guac.getDisplay().getElement());

// Send port messages
function sendGuacamoleErrorMsg(msg) {
    msg_json = { "GuacamoleMsg": msg }
    app.ports.messageReceiver.send(msg_json)
}

guac.onstatechange = function (state) {
    const state_msg = 'new state=' + state;
    sendGuacamoleErrorMsg(state_msg);
}

// Send errors to Elm port
guac.onerror = function (error) {
    const error_msg = 'guac error (status=' + error.code.toString() + ') - ' + error.message;
    sendGuacamoleErrorMsg(error_msg);
};

// Disconnect on close
window.onunload = function () {
    // TODO wire this up with ELM
    guac.disconnect();
    socket.close();
}

// Mouse and keyboard events on focus / unfocus
const mouse = new Guacamole.Mouse(guac.getDisplay().getElement());
const keyboard = new Guacamole.Keyboard(document);

// Focus guacamole element including key and mouse events
function focusGuacamole() {
    document.activeElement.blur();
    // Mouse
    mouse.onmousedown =
        mouse.onmouseup =
        mouse.onmousemove = function (mouseState) {
            guac.sendMouseState(mouseState);
        };

    keyboard.onkeydown = function (keysym) {
        guac.sendKeyEvent(1, keysym);
    };

    keyboard.onkeyup = function (keysym) {
        guac.sendKeyEvent(0, keysym);
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
    connectWebsocket(connection);
});

// Change the URL upon request, inform app of the change.
app.ports.pushUrl.subscribe(function (url) {
    window.location.hash = url;
    history.pushState({}, '', url);
    app.ports.onUrlChange.send(location.href);
});

function connectGuacamole(connection) {
    param = "port=" + connection.vncPort.toString()
    guac.connect(param);
}

// Init Websocket
const socket = new WebSocket('ws://scanner.psi.live/ws/addSocket');

// Event listeners
socket.addEventListener("message", function (event) {
    try {
        app.ports.messageReceiver.send(JSON.parse(event.data));
    } catch (SyntaxError) {
        msg_json = { "SocketError": "Syntax error in socket message from server." }
        app.ports.messageReceiver.send(msg_json)
    }
});
socket.addEventListener("close", function (event) {
    msg_json = { "SocketError": "Websocket closed." }
    app.ports.messageReceiver.send(msg_json)
})

function connectWebsocket(connection) {
    if (socket.readyState === 1) {
        socket.send(connection.containerId);
    } else {
        msg_json = { "SocketError": "Websocket not available, ignoring all messages." }
        app.ports.messageReceiver.send(msg_json)
    }
}

// disconnect from guacamole
app.ports.disconnectTunnel.subscribe(function () {
    guac.disconnect();
});
