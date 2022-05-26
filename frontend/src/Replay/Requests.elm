module Replay.Requests exposing (getAllScans)

import Http exposing (Metadata)
import Http.Detailed exposing (Error, expectJson)
import Replay.Data as Data exposing (ScansInfo)
import Requests exposing (managerApi)


getAllScans : (Result (Error String) ( Metadata, ScansInfo ) -> msg) -> Cmd msg
getAllScans m =
    Http.get
        { url = managerApi "get_all_scans"
        , expect = expectJson m Data.scansDecoder
        }
