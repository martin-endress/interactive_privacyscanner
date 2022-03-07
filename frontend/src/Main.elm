module Main exposing (main)

import Browser
import Html exposing (Html, div, text)
import Html.Attributes exposing (class)
import Page.ScanPage
import Route exposing (Route)


type alias Model =
    { page : Page
    , currentRoute : Maybe Route
    }


type Page
    = Blank
    | ScanPage Page.ScanPage.Model


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
    let
        scanModel =
            Page.ScanPage.init
    in
    { page = ScanPage scanModel
    , currentRoute = Just Route.Status
    }


view : Model -> Html Msg
view model =
    viewPage model


viewPage : Model -> Html Msg
viewPage model =
    case model.page of
        Blank ->
            text ""

        ScanPage subModel ->
            Page.ScanPage.view subModel
                |> Html.map ScanPageMsg


type Msg
    = ScanPageMsg Page.ScanPage.Msg


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    updatePage msg model


updatePage : Msg -> Model -> ( Model, Cmd Msg )
updatePage msg model =
    let
        page =
            model.page

        toPage toModel toMsg subUpdate subMsg subModel =
            let
                ( newModel, newCmd ) =
                    subUpdate subMsg subModel
            in
            ( { model | page = toModel newModel }, Cmd.map toMsg newCmd )
    in
    case ( page, msg ) of
        ( Blank, _ ) ->
            ( model, Cmd.none )

        ( ScanPage subModel, ScanPageMsg subMsg ) ->
            toPage ScanPage ScanPageMsg Page.ScanPage.update subMsg subModel


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.none
