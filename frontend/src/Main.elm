module Main exposing (main)

import Browser
import Html exposing (Html, text)
import Route exposing (Route)


type alias Model =
    { page : Page
    , currentRoute : Maybe Route
    }


type Page
    = Blank


main : Program () Model Msg
main =
    Browser.element
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }


init : () -> ( Model, Cmd Msg )
init _ =
    ( initModel, Cmd.none )


initModel : Model
initModel =
    { page = Blank
    , currentRoute = Just Route.Status
    }


view : Model -> Html msg
view model =
    text "asdff"


type Msg
    = VNC


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    updatePage msg model


updatePage : Msg -> Model -> ( Model, Cmd Msg )
updatePage msg model =
    let
        page =
            model.page
    in
    ( model, Cmd.none )


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none
