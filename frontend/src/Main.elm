module Main exposing (main)

import Browser
import Html exposing (Html, text)
import Route exposing (Route)
import Scan.Page as ScanPage


type alias Model =
    { page : Page
    , currentRoute : Maybe Route
    }


type Msg
    = ScanPageMsg ScanPage.Msg


type Page
    = Blank
    | ScanPage ScanPage.Model



-- MAIN


main : Program () Model Msg
main =
    Browser.element
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



-- INIT


init : () -> ( Model, Cmd Msg )
init _ =
    ( initModel, Cmd.none )


initModel : Model
initModel =
    let
        scanModel =
            ScanPage.init
    in
    { page = ScanPage scanModel
    , currentRoute = Just Route.Status
    }



-- VIEW


view : Model -> Html Msg
view model =
    viewPage model


viewPage : Model -> Html Msg
viewPage model =
    case model.page of
        Blank ->
            text ""

        ScanPage subModel ->
            ScanPage.view subModel
                |> Html.map ScanPageMsg



-- UPDATE


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
            toPage ScanPage ScanPageMsg ScanPage.update subMsg subModel



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.map ScanPageMsg ScanPage.messageSubscription
