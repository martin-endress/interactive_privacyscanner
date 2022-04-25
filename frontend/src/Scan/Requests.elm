module Scan.Requests exposing (registerUserInteraction, startScan)

import Bytes exposing (Bytes)
import Http exposing (Metadata)
import Http.Detailed exposing (Error, expectJson, expectWhatever)
import Json.Decode as D
import Json.Encode as E
import Scan.Data exposing (ContainerStartInfo)


managerApi : String -> String
managerApi path =
    "http://scanner.psi.test/api/" ++ path



-- REQUESTS


startScan : (Result (Error String) ( Metadata, ContainerStartInfo ) -> msg) -> String -> Cmd msg
startScan m scanUrl =
    let
        resultDecoder =
            D.map2 ContainerStartInfo
                (D.field "vnc_port" D.int)
                (D.field "container_id" D.string)
    in
    Http.post
        { url = managerApi "start_scan"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "url", E.string scanUrl ) ]
        , expect = expectJson m resultDecoder
        }


registerUserInteraction : (Result (Error Bytes) () -> msg) -> String -> Cmd msg
registerUserInteraction m containerId =
    Http.post
        { url = managerApi "register_interaction"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "container_id", E.string containerId ) ]
        , expect = expectWhatever m
        }
