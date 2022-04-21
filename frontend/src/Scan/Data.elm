module Scan.Data exposing (ContainerStartInfo, ScanStatus(..), ServerError, errorFromResponse)

import Http.Detailed exposing (Error(..))
import String exposing (fromInt)


type alias ContainerStartInfo =
    { vnc_port : Int
    , container_id : String
    }


type alias ServerError =
    { msg : String
    }


type ScanStatus
    = Idle
    | StartingContainer String
    | Connecting ContainerStartInfo
    | GuacamoleConnected


errorFromResponse : Error String -> ServerError
errorFromResponse err =
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
