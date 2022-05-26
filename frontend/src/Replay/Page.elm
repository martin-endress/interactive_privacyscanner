module Replay.Page exposing (..)

import Html exposing (Html, button, div, text)
import Html.Attributes exposing (class)
import Html.Events exposing (onClick)
import Http exposing (Metadata)
import Http.Detailed exposing (Error)
import Replay.Data exposing (ScansInfo)
import Replay.Requests as Requests



-- MODEL


type alias Model =
    { scans : ScansInfo
    }


type Msg
    = ScansInfo
    | GotScansInfo (Result (Error String) ( Metadata, ScansInfo ))



-- INIT


init : Model
init =
    { scans = []
    }



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ScansInfo ->
            ( model, Requests.getAllScans GotScansInfo )

        GotScansInfo scansInfo ->
            case scansInfo of
                Ok ( _, info ) ->
                    ( { model | scans = info }
                    , Cmd.none
                    )

                Err m ->
                    let
                        _ =
                            Debug.log "Could not retrieve scans." m
                    in
                    ( model, Cmd.none )



-- VIEW


view : Model -> Html Msg
view model =
    div
        [ class "container-fluid" ]
        [ div [ class "row", class "justify-content-center" ]
            [ text <| "#Scans:" ++ String.fromInt (List.length model.scans)
            , button
                [ class "btn"
                , class "btn-secondary"
                , class "col"
                , class "m-1"
                , onClick ScansInfo
                ]
                [ text "Update List" ]
            ]
        ]
