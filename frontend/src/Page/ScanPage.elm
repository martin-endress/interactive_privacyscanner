module Page.ScanPage exposing (..)

import Html exposing (Html, div, text)
import Html.Attributes exposing (class)


type alias Model =
    { asdf : Int
    }


type Msg
    = Empty


init : Model
init =
    { asdf = 3 }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    ( model, Cmd.none )


view : Model -> Html Msg
view model =
    div [ class "container-fluid" ] [ text "asdfff" ]
