port module Scan.Page exposing (..)

import Bytes exposing (Bytes)
import Delay
import Html exposing (Html, b, button, dd, div, dl, dt, h2, input, label, li, text, ul)
import Html.Attributes exposing (attribute, class, classList, disabled, style)
import Html.Events exposing (onClick, onInput, onMouseEnter, onMouseLeave)
import Http exposing (Metadata)
import Http.Detailed exposing (Error)
import Json.Decode as D
import Json.Encode as E
import Scan.Data as Data exposing (ContainerStartInfo, ScanState(..), ScanUpdate(..), ServerError, scanUpdateToString)
import Scan.Requests as Requests



-- MODEL


type alias Model =
    { scanState : ScanState
    , connection : Maybe Connection
    , interactionCount : Int
    , urlInput : String
    , currentUrl : String
    , guacamoleFocus : Bool
    , errors : List ServerError
    , log : List String
    }


type alias Connection =
    { vncPort : Int
    , containerId : String
    }


type Msg
    = Empty
    | UpdateUrlInput String
    | SetGuacamoleFocus Bool
    | StartScan
    | GotStartScan (Result (Error String) ( Metadata, ContainerStartInfo ))
    | ConnectToGuacamole
    | ReceiveScanUpdate ScanUpdate
    | RegisterInteraction
    | GotRequestResult (Maybe ScanState) (Result (Error Bytes) ())
    | FinishScan
    | TakeScreenshot
    | ClearBrowserCookies



-- PORTS


port connectTunnel : E.Value -> Cmd msg


port disconnectTunnel : () -> Cmd msg


port setGuacamoleFocus : Bool -> Cmd msg


port messageReceiver : (D.Value -> msg) -> Sub msg



-- INIT


init : Model
init =
    { scanState = Idle
    , connection = Nothing
    , interactionCount = 0
    , currentUrl = ""
    , urlInput = ""
    , guacamoleFocus = False
    , errors = []
    , log = []
    }



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Empty ->
            ( model, Cmd.none )

        UpdateUrlInput newUrl ->
            ( { model
                | urlInput = newUrl
              }
            , Cmd.none
            )

        SetGuacamoleFocus focus ->
            ( { model | guacamoleFocus = focus }
            , setGuacamoleFocus focus
            )

        StartScan ->
            ( updateScanState ConnectingToBrowser model
            , Requests.startScan GotStartScan model.urlInput
            )

        GotStartScan result ->
            processStartResult model result

        ConnectToGuacamole ->
            let
                encodeConnection connection =
                    E.object
                        [ ( "vncPort", E.int connection.vncPort )
                        , ( "containerId", E.string connection.containerId )
                        ]
            in
            ( model
            , model.connection
                |> Maybe.map encodeConnection
                |> Maybe.map connectTunnel
                |> Maybe.withDefault Cmd.none
            )

        ReceiveScanUpdate scanUpdate ->
            ( processScanUpdate scanUpdate model
            , Cmd.none
            )

        RegisterInteraction ->
            ( model
            , model.connection
                |> Maybe.map .containerId
                |> Maybe.map (Requests.registerUserInteraction <| GotRequestResult (Just ScanInProgress))
                |> Maybe.withDefault Cmd.none
            )

        GotRequestResult newScanState result ->
            ( processRequestResult result newScanState model
            , Cmd.none
            )

        FinishScan ->
            ( model
            , finishScanCommands model
            )

        TakeScreenshot ->
            ( model
            , model.connection
                |> Maybe.map .containerId
                |> Maybe.map (Requests.takeScreenshot <| GotRequestResult Nothing)
                |> Maybe.withDefault Cmd.none
            )

        ClearBrowserCookies ->
            ( model
            , model.connection
                |> Maybe.map .containerId
                |> Maybe.map (Requests.clearBrowserCookies <| GotRequestResult Nothing)
                |> Maybe.withDefault Cmd.none
            )


finishScanCommands : Model -> Cmd Msg
finishScanCommands model =
    let
        finishCmd =
            model.connection
                |> Maybe.map .containerId
                |> Maybe.map (Requests.finishScan <| GotRequestResult (Just FinalScanInProgress))
                |> Maybe.withDefault Cmd.none
    in
    Cmd.batch [ finishCmd, disconnectTunnel () ]


processStartResult : Model -> Result (Error String) ( Metadata, ContainerStartInfo ) -> ( Model, Cmd Msg )
processStartResult model result =
    case result of
        Ok ( _, containerInfo ) ->
            let
                connection =
                    { vncPort = containerInfo.vnc_port
                    , containerId = containerInfo.container_id
                    }
            in
            ( updateScanState ScanInProgress
                { model
                    | connection = Just connection
                }
            , Delay.after 3000 ConnectToGuacamole
            )

        Err error ->
            ( { model
                | errors = Data.errorFromStringResponse error :: model.errors
              }
            , Cmd.none
            )


processScanUpdate : ScanUpdate -> Model -> Model
processScanUpdate scanUpdate model =
    case ( scanUpdate, model.scanState ) of
        ( NoOp, _ ) ->
            model

        ( ScanComplete, ScanInProgress ) ->
            updateScanState AwaitingInteraction { model | interactionCount = model.interactionCount + 1 }

        ( ScanComplete, FinalScanInProgress ) ->
            init

        ( SocketError message, _ ) ->
            appendError { msg = "VNC error:" ++ message } model

        ( GuacamoleError message, _ ) ->
            appendError { msg = "Guacamole error:" ++ message } model

        ( Log message, _ ) ->
            appendLog message model

        ( URLChanged newUrl, _ ) ->
            -- todo
            { model | currentUrl = newUrl }

        ( _, _ ) ->
            -- Illegal state
            appendError
                { msg =
                    "Illegal State. (msg="
                        ++ scanUpdateToString scanUpdate
                        ++ ", state="
                        ++ Data.stateToString model.scanState
                        ++ ")"
                }
                model


processRequestResult : Result (Error Bytes) () -> Maybe ScanState -> Model -> Model
processRequestResult result newScanState =
    case result of
        Ok _ ->
            case newScanState of
                Just state ->
                    updateScanState state

                Nothing ->
                    identity

        Err error ->
            appendError (Data.errorFromResponse error)


updateScanState : ScanState -> Model -> Model
updateScanState newState model =
    { model | scanState = newState }


appendError : ServerError -> Model -> Model
appendError err model =
    { model
        | errors = err :: model.errors
    }


appendLog : String -> Model -> Model
appendLog msg model =
    { model | log = msg :: model.log }



-- SUBSCRIPTIONS


messageSubscription : Sub Msg
messageSubscription =
    messageReceiver Data.mapScanUpdated
        |> Sub.map ReceiveScanUpdate



-- VIEW


view : Model -> Html Msg
view model =
    div
        [ class "container-fluid" ]
        [ h2 [] [ text "Interactive Privacy Scanner" ]
        , viewStartInput model
        , div [ class "row m-2", style "height" "1000px" ]
            [ viewGuacamoleDisplay model
            , viewStatusPanel model
            ]
        ]


viewStartInput : Model -> Html Msg
viewStartInput model =
    div [ class "row m-2" ]
        [ div [ class "col-md-6 mx-auto" ]
            [ label
                [ attribute "for" "url_input" ]
                [ text "Enter URL to perform an interactive scan:" ]
            , div [ class "input-group mb-3" ]
                [ input
                    [ attribute "type" "text"
                    , class "form-control"
                    , attribute "id" "url_input"
                    , attribute
                        "aria-describedby"
                        "basic-addon3"
                    , attribute
                        "placeholder"
                        "url, e.g. uni-bamberg.de"
                    , onInput UpdateUrlInput
                    ]
                    [ text model.urlInput ]
                , button
                    [ class "btn btn-primary"
                    , attribute "type" "button"
                    , onClick StartScan
                    ]
                    [ text "Start Scan" ]
                ]
            ]
        ]


viewGuacamoleDisplay : Model -> Html Msg
viewGuacamoleDisplay model =
    let
        visibility =
            if model.scanState == Idle then
                "hidden"

            else
                "visible"
    in
    div
        [ attribute "id" "display"
        , classList
            [ ( "col", True )
            , ( "border", model.guacamoleFocus )
            , ( "border-success", model.guacamoleFocus )
            , ( "border-2", model.guacamoleFocus )
            ]
        , style "visibility" visibility
        , onMouseEnter (SetGuacamoleFocus True)
        , onMouseLeave (SetGuacamoleFocus False)
        ]
        []


viewStatusPanel : Model -> Html Msg
viewStatusPanel model =
    let
        awaitingInteraction =
            model.scanState == AwaitingInteraction
    in
    div
        [ class "col-md-4", class "bg-light" ]
        [ descriptionList
            [ ( "Status", Data.stateToString model.scanState )
            , ( "Current URL", model.currentUrl )
            , ( "Interactions", String.fromInt model.interactionCount )
            ]
        , viewErrors model.errors
        , viewLogs model.log
        , div [ class "row", class "m-2" ]
            [ button
                [ class "btn"
                , class "btn-secondary"
                , class "col-sm"
                , class "mx-1"
                , onClick TakeScreenshot
                , disabled <| not awaitingInteraction
                ]
                [ text "Take Screenshot" ]
            , button
                [ class "btn"
                , class "btn-secondary"
                , class "col-sm"
                , class "mx-1"
                , onClick ClearBrowserCookies
                , disabled <| not awaitingInteraction
                ]
                [ text "Clear Cookies" ]
            ]
        , div
            [ class "row", class "m-2" ]
            [ button
                [ class "btn"
                , class "btn-primary"
                , onClick RegisterInteraction
                , disabled <| not awaitingInteraction
                ]
                [ text "Register User Interaction" ]
            ]
        , div [ class "row", class "m-2" ]
            [ button
                [ class "btn"
                , class "btn-success"
                , onClick FinishScan
                , disabled <| not awaitingInteraction
                ]
                [ text "Finish Scan" ]
            ]
        ]


descriptionList : List ( String, String ) -> Html Msg
descriptionList items =
    dl [ class "row", class "m-2" ]
        (items
            |> List.map descriptionListItem
            |> List.concat
        )


descriptionListItem : ( String, String ) -> List (Html Msg)
descriptionListItem ( k, v ) =
    [ dt [ class "col-sm-3" ] [ text k ]
    , dd [ class "col-sm-9" ] [ text v ]
    ]


viewErrors : List ServerError -> Html Msg
viewErrors serverErrors =
    let
        viewErrorEntry e =
            li [ class "list-group-item-danger" ] [ text e.msg ]
    in
    div
        [ class "row", class "m-2" ]
        [ div [ class "col-sm-3" ] [ b [] [ text "Errors" ] ]
        , if List.isEmpty serverErrors then
            div [ class "col-sm-9" ] [ text "no errors :)" ]

          else
            ul [ class "col", class "list-group" ] <|
                List.map viewErrorEntry serverErrors
        ]


viewLogs : List String -> Html Msg
viewLogs log =
    let
        viewLogEntry e =
            li [ class "list-group-item-info" ] [ text e ]
    in
    div
        [ class "row", class "m-2" ]
        [ div [ class "col-sm-3" ] [ b [] [ text "Log" ] ]
        , if List.isEmpty log then
            text ""

          else
            ul [ class "col", class "list-group" ] <|
                List.map viewLogEntry log
        ]
