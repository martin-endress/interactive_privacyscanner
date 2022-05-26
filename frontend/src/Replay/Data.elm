module Replay.Data exposing (Scan, ScansInfo,scansDecoder)

import Json.Decode as D exposing (Decoder)


type alias ScansInfo =
    List Scan


type alias Scan =
    { id : String
    , replayCount : Int
    }


scansDecoder : Decoder ScansInfo
scansDecoder =
    D.map2 Scan
        (D.field "id" D.string)
        (D.field "replay_count" D.int)
        |> D.list
