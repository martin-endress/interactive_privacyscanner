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
    Http.post
        { url = managerApi "start_scan"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "url", E.string scanUrl ) ]
        , expect = expectJson m startContainerResultDecoder
        }


startContainerResultDecoder : D.Decoder ContainerStartInfo
startContainerResultDecoder =
    D.map2 ContainerStartInfo
        (D.field "vnc_port" D.int)
        (D.field "container_id" D.string)


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
