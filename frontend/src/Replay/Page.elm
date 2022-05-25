module Replay.Page exposing (..)

import Html exposing (Html, div, text)
import Html.Attributes exposing (class)



-- MODEL


type alias Model =
    { scans : List String
    }


type Msg
    = Empty



-- INIT


init : Model
init =
    { scans = []
    }



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    ( model, Cmd.none )



-- VIEW


view : Model -> Html Msg
view model =
    div
        [ class "container-fluid" ]
        [ div [ class "row", class "justify-content-center" ]
            [ text "asdf"
            ]
        ]
