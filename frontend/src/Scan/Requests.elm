module Scan.Requests exposing (clearBrowserCookies, finishScan, registerUserInteraction, startScan, takeScreenshot)

import Bytes exposing (Bytes)
import Http exposing (Metadata)
import Http.Detailed exposing (Error, expectJson, expectWhatever)
import Json.Decode as D
import Json.Encode as E
import Requests exposing (managerApi)
import Scan.Data exposing (ContainerStartInfo)


startScan : (Result (Error String) ( Metadata, ContainerStartInfo ) -> msg) -> String -> String -> Cmd msg
startScan m scanUrl socketToken =
    let
        resultDecoder =
            D.map ContainerStartInfo
                (D.field "session" D.string)
    in
    Http.post
        { url = managerApi "start_scan"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "url", E.string scanUrl )
                    , ( "socket_token", E.string socketToken )
                    ]
        , expect = expectJson m resultDecoder
        }


registerUserInteraction : (Result (Error Bytes) () -> msg) -> String -> Cmd msg
registerUserInteraction m session_id =
    Http.post
        { url = managerApi "register_interaction"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "session_id", E.string session_id ) ]
        , expect = expectWhatever m
        }


finishScan : (Result (Error Bytes) () -> msg) -> String -> String -> Cmd msg
finishScan m note session_id =
    Http.post
        { url = managerApi "stop_scan"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "session_id", E.string session_id )
                    , ( "scan_note", E.string note )
                    ]
        , expect = expectWhatever m
        }


clearBrowserCookies : (Result (Error Bytes) () -> msg) -> String -> Cmd msg
clearBrowserCookies m session_id =
    Http.post
        { url = managerApi "clear_cookies"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "session_id", E.string session_id ) ]
        , expect = expectWhatever m
        }


takeScreenshot : (Result (Error Bytes) () -> msg) -> String -> Cmd msg
takeScreenshot m session_id =
    Http.post
        { url = managerApi "take_screenshot"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "session_id", E.string session_id ) ]
        , expect = expectWhatever m
        }
