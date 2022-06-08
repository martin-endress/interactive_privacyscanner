module Results.Requests exposing (downloadAllResults, downloadResult, getAllScans, replayScan)

import File.Download as Download
import Http exposing (Metadata)
import Http.Detailed exposing (Error, expectJson)
import Json.Decode as D
import Json.Encode as E
import Requests exposing (managerApi)
import Results.Data as Data exposing (ScanInfo)


getAllScans : (Result (Error String) ( Metadata, List ScanInfo ) -> msg) -> Cmd msg
getAllScans m =
    Http.get
        { url = managerApi "get_all_scans"
        , expect = expectJson m Data.scansDecoder
        }


replayScan : (Result (Error String) ( Metadata, Int ) -> msg) -> String -> Cmd msg
replayScan m resultId =
    let
        resultDecoder =
            D.field "vnc_port" D.int
    in
    Http.post
        { url = managerApi "replay_scan"
        , body =
            Http.jsonBody <|
                E.object
                    [ ( "result_id", E.string resultId ) ]
        , expect = expectJson m resultDecoder
        }


downloadResult : String -> Cmd msg
downloadResult resultId =
    Download.url <| managerApi "result" ++ "/" ++ resultId


downloadAllResults : Cmd msg
downloadAllResults =
    Download.url <| managerApi "results"
