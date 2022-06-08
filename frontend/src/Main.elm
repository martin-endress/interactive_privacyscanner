module Main exposing (main)

import Browser
import Html exposing (Html)
import Results.Page as ResultsPage
import Scan.Page as ScanPage


type alias Model =
    { page : Page
    }


type Msg
    = ScanPageMsg ScanPage.Msg
    | ResultsPageMsg ResultsPage.Msg


type Page
    = ScanPage ScanPage.Model
    | ResultsPage ResultsPage.Model



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
    ( initModelScanner, Cmd.none )


initModelScanner : Model
initModelScanner =
    { page = ScanPage ScanPage.init
    }


initModelResults : Model
initModelResults =
    { page = ResultsPage ResultsPage.init
    }



-- VIEW


view : Model -> Html Msg
view model =
    viewPage model


viewPage : Model -> Html Msg
viewPage model =
    case model.page of
        ScanPage subModel ->
            ScanPage.view subModel
                |> Html.map ScanPageMsg

        ResultsPage subModel ->
            ResultsPage.view subModel |> Html.map ResultsPageMsg



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    updatePage msg model


updatePage : Msg -> Model -> ( Model, Cmd Msg )
updatePage msg model =
    case ( model.page, msg ) of
        ( ScanPage subModel, ScanPageMsg subMsg ) ->
            case subMsg of
                ScanPage.ViewResults ->
                    -- swich page
                    ( initModelResults, Cmd.none )

                _ ->
                    let
                        ( newModel, newCmd ) =
                            ScanPage.update subMsg subModel
                    in
                    ( { model | page = ScanPage newModel }, Cmd.map ScanPageMsg newCmd )

        ( ResultsPage subModel, ResultsPageMsg subMsg ) ->
            case subMsg of
                ResultsPage.ViewScanner ->
                    -- swich page
                    ( initModelScanner, Cmd.none )

                _ ->
                    let
                        ( newModel, newCmd ) =
                            ResultsPage.update subMsg subModel
                    in
                    ( { model | page = ResultsPage newModel }, Cmd.map ResultsPageMsg newCmd )

        _ ->
            ( model, Cmd.none )


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.map ScanPageMsg ScanPage.messageSubscription
