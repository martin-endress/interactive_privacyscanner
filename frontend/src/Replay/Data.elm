module Replay.Data exposing (Scan, ScansInfo)


type alias ScansInfo =
    List Scan


type alias Scan =
    { id : String
    , replayCount : Int
    }
