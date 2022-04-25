module Scan.Data exposing (ContainerStartInfo, ScanStatus(..), ScanUpdate(..), ServerError, errorFromResponse, errorFromStringResponse, mapScanUpdated, statusToString)

import Http.Detailed exposing (Error(..))
import Json.Decode as D exposing (Decoder)
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


type ScanStatus
    = Idle
    | ConnectingToBrowser
    | InitialScanInProgress
    | AwaitingInteraction
    | ScanInProgress


statusToString : ScanStatus -> String
statusToString status =
    case status of
        Idle ->
            "No site selected, please select an URL."

        ConnectingToBrowser ->
            "Connecting to browser, please wait."

        InitialScanInProgress ->
            "Initial scan in progress, please wait."

        AwaitingInteraction ->
            "Awaiting user input."

        ScanInProgress ->
            "Scan in progress, please wait."


type ScanUpdate
    = NoOp
    | ScanComplete
    | GuacamoleError String
    | URLChanged String


mapScanUpdated : D.Value -> ScanUpdate
mapScanUpdated msgJson =
    case decodeMsg msgJson of
        Ok stateMsg ->
            stateMsg

        Err errorMessage ->
            let
                _ =
                    Debug.log "Error in mapScanUpdated:" errorMessage
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

        _ ->
            Nothing
