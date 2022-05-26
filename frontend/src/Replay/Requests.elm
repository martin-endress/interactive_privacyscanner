module Replay.Requests exposing (getAllScans)

import Http exposing (Metadata)
import Http.Detailed exposing (Error, expectJson)
import Json.Decode as D
import Replay.Data exposing (Scan, ScansInfo)
import Requests exposing (managerApi)


getAllScans : (Result (Error String) ( Metadata, ScansInfo ) -> msg) -> Cmd msg
getAllScans m =
    let
        resultDecoder =
            D.map2 Scan
                (D.field "id" D.string)
                (D.field "replay_count" D.int)
                |> D.list
    in
    Http.get
        { url = managerApi "get_all_scans"
        , expect = expectJson m resultDecoder
        }
