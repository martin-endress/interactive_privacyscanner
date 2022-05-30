port module Ports exposing (connectTunnel, disconnectTunnel, messageReceiver, onUrlChange, pushUrl, setGuacamoleFocus)

import Json.Decode as D
import Json.Encode as E


port connectTunnel : E.Value -> Cmd msg


port disconnectTunnel : () -> Cmd msg


port setGuacamoleFocus : Bool -> Cmd msg


port onUrlChange : (String -> msg) -> Sub msg


port pushUrl : String -> Cmd msg


port messageReceiver : (D.Value -> msg) -> Sub msg
