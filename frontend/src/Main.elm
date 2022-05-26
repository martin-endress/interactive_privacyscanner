module Main exposing (main)

import Browser
import Html exposing (Html)
import Ports
import Replay.Page as ReplayPage
import Route exposing (Route(..))
import Scan.Page as ScanPage


type alias Model =
    { page : Page
    , route : Route
    }


type Msg
    = ChangedUrl String
    | ScanPageMsg ScanPage.Msg
    | ReplayPageMsg ReplayPage.Msg


type Page
    = ScanPage ScanPage.Model
    | ReplayPage ReplayPage.Model



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
    ( initModel, Route.modifyUrl Route.Scanner )


initModel : Model
initModel =
    { page = ScanPage ScanPage.init
    , route = Scanner
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

        ReplayPage subModel ->
            ReplayPage.view subModel |> Html.map ReplayPageMsg



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
        ( _, ChangedUrl url ) ->
            setRoute (Route.toRoute url) model

        ( ScanPage subModel, ScanPageMsg subMsg ) ->
            toPage ScanPage ScanPageMsg ScanPage.update subMsg subModel

        ( ReplayPage subModel, ReplayPageMsg subMsg ) ->
            toPage ReplayPage ReplayPageMsg ReplayPage.update subMsg subModel

        bad_state ->
            let
                _ =
                    Debug.log "Error in updatePage. Unexpected Update message received." bad_state
            in
            ( model, Cmd.none )


setRoute : Route -> Model -> ( Model, Cmd Msg )
setRoute route model =
    let
        newModel =
            { model | route = route }
    in
    case route of
        NotFound ->
            ( newModel
            , Cmd.none
            )

        Scanner ->
            ( { newModel | page = ScanPage ScanPage.init }
            , Cmd.none
            )

        Replay ->
            ( { model | page = ReplayPage ReplayPage.init }
            , Cmd.none
            )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.batch
        [ Sub.map ScanPageMsg ScanPage.messageSubscription, Ports.onUrlChange ChangedUrl ]
