module Scan.Data exposing (ContainerStartInfo, ScanState(..), ScanUpdate(..), ServerError, errorFromResponse, errorFromStringResponse, mapScanUpdated, scanUpdateToString, stateToString)

import Http.Detailed exposing (Error(..))
import Json.Decode as D exposing (Decoder)
import Json.Encode as E
import String exposing (fromInt)


type alias ContainerStartInfo =
    { vnc_port : Int
    , container_id : String
    }


type alias ServerError =
    { msg : String
    }


errorFromResponse : Error a -> ServerError
errorFromResponse err =
    case err of
        BadUrl url ->
            { msg = "Bad input URL: " ++ url }

        Timeout ->
            { msg = "Server Timeout" }

        NetworkError ->
            { msg = "Network Error" }

        BadStatus meta _ ->
            { msg = "Bad Status " ++ fromInt meta.statusCode }

        BadBody meta _ str ->
            { msg =
                "Bad Body, parsing not possible: "
                    ++ str
                    ++ " (status="
                    ++ fromInt meta.statusCode
                    ++ ")"
            }


errorFromStringResponse : Error String -> ServerError
errorFromStringResponse err =
    case err of
        BadUrl url ->
            { msg = "Bad input URL: " ++ url }

        Timeout ->
            { msg = "Server Timeout" }

        NetworkError ->
            { msg = "Network Error" }

        BadStatus meta body ->
            { msg = "Bad Status " ++ fromInt meta.statusCode ++ ": " ++ body }

        BadBody meta body str ->
            { msg =
                "Bad Body, parsing not possible: "
                    ++ body
                    ++ ", "
                    ++ str
                    ++ " (status="
                    ++ fromInt meta.statusCode
                    ++ ")"
            }


type ScanState
    = Idle
    | ConnectingToBrowser
    | ScanInProgress
    | AwaitingInteraction
    | FinalScanInProgress


stateToString : ScanState -> String
stateToString status =
    case status of
        Idle ->
            "No site selected, please select an URL."

        ConnectingToBrowser ->
            "Connecting to browser, please wait."

        ScanInProgress ->
            "Scan in progress, please wait."

        AwaitingInteraction ->
            "Awaiting user input."

        FinalScanInProgress ->
            "Final Scan in progress."


type ScanUpdate
    = NoOp
    | ScanComplete
    | SocketError String
    | Log String
    | GuacamoleError String
    | URLChanged String


scanUpdateToString : ScanUpdate -> String
scanUpdateToString update =
    case update of
        NoOp ->
            "NoOp"

        ScanComplete ->
            "ScanComplete"

        SocketError _ ->
            "SocketError"

        Log _ ->
            "Log"

        GuacamoleError _ ->
            "GuacamoleError"

        URLChanged _ ->
            "URLChanged"


mapScanUpdated : D.Value -> ScanUpdate
mapScanUpdated msgJson =
    case decodeMsg msgJson of
        Ok stateMsg ->
            stateMsg

        Err errorMessage ->
            let
                _ =
                    Debug.log "Illegal message detected:" ( errorMessage, E.encode 2 msgJson )
            in
            NoOp


decodeMsg : D.Value -> Result D.Error ScanUpdate
decodeMsg msg =
    D.decodeValue scanUpdateDecoder msg


scanUpdateDecoder : Decoder ScanUpdate
scanUpdateDecoder =
    D.keyValuePairs D.string
        |> D.map List.head
        |> onlyJusts
        |> D.map scanUpdateFromDict
        |> onlyJusts


onlyJusts : Decoder (Maybe a) -> Decoder a
onlyJusts =
    D.andThen
        (\m ->
            m
                |> Maybe.map D.succeed
                |> Maybe.withDefault (D.fail "Decoding failed, key value pair not valid.")
        )


scanUpdateFromDict : ( String, String ) -> Maybe ScanUpdate
scanUpdateFromDict ( k, v ) =
    case k of
        "ScanComplete" ->
            Just ScanComplete

        "GuacamoleError" ->
            Just (GuacamoleError v)

        "URLChanged" ->
            Just (URLChanged v)

        "Log" ->
            Just (Log v)

        _ ->
            Nothing
