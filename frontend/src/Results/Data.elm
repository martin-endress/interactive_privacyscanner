module Results.Data exposing (ScanInfo, scansDecoder)

import Json.Decode as D exposing (Decoder)


type alias ScanInfo =
    { id : String
    , initialScan : InitialScanInfo
    , replays : List ScanReplayInfo
    }


type alias InitialScanInfo =
    { success : Bool
    }


type alias ScanReplayInfo =
    { success : Bool
    }


scansDecoder : Decoder (List ScanInfo)
scansDecoder =
    D.map3 ScanInfo
        (D.field "id" D.string)
        (D.field "initial" initialScanDecoder)
        (D.field "replays" replayScanDecoder)
        |> D.list


initialScanDecoder : Decoder InitialScanInfo
initialScanDecoder =
    D.map
        ScanReplayInfo
        (D.field "success" D.bool)


replayScanDecoder : Decoder (List ScanReplayInfo)
replayScanDecoder =
    D.map
        ScanReplayInfo
        (D.field "success" D.bool)
        |> D.list
