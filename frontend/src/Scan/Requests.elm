module Scan.Requests exposing (startContainerInstance)

import Http exposing (Metadata)
import Http.Detailed exposing (Error, expectJson)
import Json.Decode as D
import Json.Encode as E
import Scan.Data exposing (ContainerStartInfo)


startContainerInstance : (Result (Error String) ( Metadata, ContainerStartInfo ) -> msg) -> String -> Cmd msg
startContainerInstance m scanUrl =
    Http.post
        { url = managerApi "start_instance"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "url", E.string scanUrl ) ]
        , expect = expectJson m startContainerResultDecoder
        }


managerApi : String -> String
managerApi path =
    "http://scanner.psi.test/api/" ++ path


startContainerResultDecoder : D.Decoder ContainerStartInfo
startContainerResultDecoder =
    D.map2 ContainerStartInfo
        (D.field "vnc_port" D.int)
        (D.field "container_id" D.string)
