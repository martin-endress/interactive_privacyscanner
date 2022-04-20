module Scan.Requests exposing (startContainerInstance)

import Http exposing (Error)
import Json.Decode as D
import Json.Encode as E
import Scan.Data exposing (ContainerStartInfo)


managerApi : String -> String
managerApi path =
    "http://scanner.psi.test/api/" ++ path


startContainerInstance : (Result Error ContainerStartInfo -> msg) -> String -> Cmd msg
startContainerInstance m scanUrl =
    Http.post
        { url = managerApi "start_instance"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "url", E.string scanUrl ) ]
        , expect = Http.expectJson m startContainerResultDecoder
        }


startContainerResultDecoder : D.Decoder ContainerStartInfo
startContainerResultDecoder =
    D.map2 ContainerStartInfo
        (D.field "vnc_port" D.int)
        (D.field "container_id" D.int)
