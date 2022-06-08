module Scan.Page exposing (..)

import Bytes exposing (Bytes)
import Delay
import Html exposing (Html, b, button, div, h4, input, text, textarea)
import Html.Attributes exposing (attribute, class, disabled, style, value)
import Html.Events exposing (onClick, onInput, onMouseEnter, onMouseLeave)
import Http exposing (Metadata)
import Http.Detailed exposing (Error)
import Json.Encode as E
import Maybe
import Ports
import Scan.Data as Data exposing (ContainerStartInfo, LogEntry, ScanState(..), ScanUpdate(..), scanUpdateToString)
import Scan.Requests as Requests
import Scan.View as View



-- MODEL


type alias Model =
    { scanState : ScanState
    , socketId : Maybe String
    , connection : Maybe Connection
    , interactionCount : Int
    , urlInput : String
    , noteInput : String
    , currentUrl : String
    , guacamoleFocus : Bool
    , log : List LogEntry
    }


type alias Connection =
    { vncPort : Int
    , containerId : String
    }


type Msg
    = UpdateUrlInput String
    | SetGuacamoleFocus Bool
    | StartScan
    | GotStartScan (Result (Error String) ( Metadata, ContainerStartInfo ))
    | ConnectToGuacamole Connection
    | ReceiveScanUpdate ScanUpdate
    | UpdateNoteInput String
    | RegisterInteraction
    | GotRequestResult (Maybe ScanState) (Result (Error Bytes) ())
    | FinishScan
    | TakeScreenshot
    | ClearBrowserCookies
    | ViewResults



-- INIT


init : Model
init =
    { scanState = Idle
    , socketId = Nothing
    , connection = Nothing
    , interactionCount = 0
    , currentUrl = ""
    , urlInput = ""
    , noteInput = ""
    , guacamoleFocus = False
    , log = []
    }


clearModel : Model -> Model
clearModel oldModel =
    -- clear model for everything except socket id (allow for repeated scans)
    { scanState = Idle
    , socketId = oldModel.socketId
    , connection = Nothing
    , interactionCount = 0
    , currentUrl = ""
    , urlInput = ""
    , noteInput = ""
    , guacamoleFocus = False
    , log = []
    }



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        UpdateUrlInput newUrl ->
            ( { model
                | urlInput = newUrl
              }
            , Cmd.none
            )

        SetGuacamoleFocus focus ->
            ( { model | guacamoleFocus = focus }
            , Ports.setGuacamoleFocus focus
            )

        StartScan ->
            startScan model

        GotStartScan result ->
            processStartResult model result

        ConnectToGuacamole connection ->
            ( appendLogEntry { msg = "Connecting to Guacamole...", level = Data.Info } model
            , Ports.connectTunnel <|
                E.object
                    [ ( "vncPort", E.int connection.vncPort )
                    , ( "containerId", E.string connection.containerId )
                    ]
            )

        ReceiveScanUpdate scanUpdate ->
            processScanUpdate scanUpdate model

        UpdateNoteInput newNoteInput ->
            ( { model | noteInput = newNoteInput }
            , Cmd.none
            )

        RegisterInteraction ->
            ( model
            , model.connection
                |> Maybe.map .containerId
                |> Maybe.map
                    (Requests.registerUserInteraction (GotRequestResult (Just ScanInProgress)))
                |> Maybe.withDefault Cmd.none
            )

        GotRequestResult newScanState result ->
            ( processRequestResult result newScanState model
            , Cmd.none
            )

        FinishScan ->
            ( clearModel model
            , finishScanCommands model
            )

        TakeScreenshot ->
            ( model
            , model.connection
                |> Maybe.map .containerId
                |> Maybe.map
                    (Requests.takeScreenshot (GotRequestResult Nothing))
                |> Maybe.withDefault Cmd.none
            )

        ClearBrowserCookies ->
            ( model
            , model.connection
                |> Maybe.map .containerId
                |> Maybe.map
                    (Requests.clearBrowserCookies (GotRequestResult (Just ScanInProgress)))
                |> Maybe.withDefault Cmd.none
            )

        ViewResults ->
            -- handled in Main
            ( model, Cmd.none )


startScan : Model -> ( Model, Cmd Msg )
startScan model =
    case model.socketId of
        Just socketId ->
            ( updateScanState ConnectingToBrowser model
            , Requests.startScan GotStartScan model.urlInput socketId
            )

        Nothing ->
            ( appendLogEntry
                { msg = "Socket not connected.", level = Data.Error }
                model
            , Cmd.none
            )


finishScanCommands : Model -> Cmd Msg
finishScanCommands model =
    let
        finishCmd =
            model.connection
                |> Maybe.map .containerId
                |> Maybe.map
                    (Requests.finishScan
                        (GotRequestResult (Just FinalScanInProgress))
                        model.noteInput
                    )
                |> Maybe.withDefault Cmd.none
    in
    Cmd.batch [ finishCmd, Ports.disconnectTunnel () ]


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
            , Delay.after 500 (ConnectToGuacamole connection)
            )

        Err error ->
            ( { model
                | log = Data.errorFromStringResponse error :: model.log
              }
            , Cmd.none
            )


processScanUpdate : ScanUpdate -> Model -> ( Model, Cmd Msg )
processScanUpdate scanUpdate model =
    case ( scanUpdate, model.scanState ) of
        ( NoOp, _ ) ->
            ( model, Cmd.none )

        ( SocketInit id, Idle ) ->
            ( { model | socketId = Just id }, Cmd.none )

        ( ScanComplete, ScanInProgress ) ->
            ( updateScanState
                AwaitingInteraction
                { model | interactionCount = model.interactionCount + 1 }
            , Cmd.none
            )

        ( ScanComplete, FinalScanInProgress ) ->
            ( clearModel model, Cmd.none )

        ( SocketError message, _ ) ->
            ( appendLogEntry
                { msg = "Socket msg:" ++ message, level = Data.Error }
                model
            , Cmd.none
            )

        ( GuacamoleMsg message, _ ) ->
            let
                cmd =
                    case scanUpdate of
                        GuacamoleMsg _ ->
                            model.connection
                                |> Maybe.map (\c -> Delay.after 500 (ConnectToGuacamole c))
                                |> Maybe.withDefault Cmd.none

                        _ ->
                            Cmd.none
            in
            ( appendLogEntry
                { msg = "Guacamole msg:" ++ message, level = Data.Warning }
                model
            , cmd
            )

        ( Log message, _ ) ->
            let
                entry =
                    { msg = message, level = Data.Info }
            in
            ( appendLogEntry entry model, Cmd.none )

        ( URLChanged newUrl, _ ) ->
            -- todo
            ( { model | currentUrl = newUrl }, Cmd.none )

        ( _, _ ) ->
            -- Illegal state
            ( appendLogEntry
                { msg =
                    "Illegal State. (msg="
                        ++ scanUpdateToString scanUpdate
                        ++ ", state="
                        ++ Data.stateToString model.scanState
                        ++ ")"
                , level = Data.Error
                }
                model
            , Cmd.none
            )


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
            appendLogEntry (Data.errorFromResponse error)


updateScanState : ScanState -> Model -> Model
updateScanState newState model =
    { model | scanState = newState }


appendLogEntry : LogEntry -> Model -> Model
appendLogEntry entry model =
    { model
        | log = entry :: model.log
    }



-- SUBSCRIPTIONS


messageSubscription : Sub Msg
messageSubscription =
    Ports.messageReceiver Data.mapScanUpdated
        |> Sub.map ReceiveScanUpdate



-- VIEW


view : Model -> Html Msg
view model =
    div
        [ class "container-fluid" ]
        [ div [ class "row", class "justify-content-center" ]
            [ viewStatusPanel model
            , viewGuacamoleDisplay model
            ]
        ]


viewStatusPanel : Model -> Html Msg
viewStatusPanel model =
    div
        [ class "col-4"
        , class "p-0"
        , class "bg-light"
        , class "vh-100"
        , class "d-flex"
        , class "flex-column"
        ]
        [ h4
            [ class "m-3", class "text-center" ]
            [ text "Interactive Privacyscanner" ]
        , viewStartInput model
        , div [ class "container", class "m-2", class "px-1" ]
            [ View.viewDescriptionText
                "Status"
                (Data.stateToString model.scanState)
            , View.viewDescriptionText
                "Current URL"
                model.currentUrl
            , View.viewDescriptionText
                "Interactions"
                (String.fromInt model.interactionCount)
            ]
        , viewButtons model
        , View.viewLog model.log
        , div
            [ class "row"
            , class "justify-content-center"
            , class "flex-grow-1"
            ]
            []
        , div [ class "container", class "m-1" ]
            [ div
                [ class "row" ]
                [ button
                    [ class "btn"
                    , class "btn-success"
                    , class "m-1"
                    , class "col"
                    , onClick ViewResults
                    ]
                    [ text "View Results" ]
                ]
            ]
        ]


viewStartInput : Model -> Html Msg
viewStartInput model =
    div [ class "mx-3" ]
        [ div [ class "input-group mb-2" ]
            [ input
                [ attribute "type" "text"
                , class "form-control"
                , attribute
                    "placeholder"
                    "Enter a URL to perform an interactive scan"
                , onInput UpdateUrlInput
                , value model.urlInput
                ]
                []
            , button
                [ class "btn btn-primary"
                , attribute "type" "button"
                , onClick StartScan
                ]
                [ text "Start Scan" ]
            ]
        ]


viewButtons : Model -> Html Msg
viewButtons model =
    let
        awaitingInteraction =
            model.scanState == AwaitingInteraction
    in
    div [ class "container", class "m-1" ]
        [ div
            [ class "row" ]
            [ button
                [ class "btn"
                , class "btn-secondary"
                , class "col"
                , class "m-1"
                , onClick TakeScreenshot
                , disabled <| not awaitingInteraction
                ]
                [ text "Take Screenshot" ]
            , button
                [ class "btn"
                , class "btn-secondary"
                , class "col"
                , class "m-1"
                , onClick ClearBrowserCookies
                , disabled <| not awaitingInteraction
                ]
                [ text "Clear Cookies" ]
            ]
        , div
            [ class "row" ]
            [ button
                [ class "btn"
                , class "btn-primary"
                , class "m-1"
                , class "col"
                , onClick RegisterInteraction
                , disabled <| not awaitingInteraction
                ]
                [ text "Register User Interaction" ]
            ]
        , div
            [ class "container"
            , class "mx-0"
            , class "px-0"
            , class "py-1"
            ]
            [ b
                [ class "row"
                , class "mx-0"
                , class "p-0"
                , class "w-100"
                ]
                [ text "Scan Notes" ]
            , textarea
                [ class "row"
                , class "mx-0"
                , class "px-0"
                , attribute "rows" "4"
                , attribute "cols" "60"
                , value model.noteInput
                , onInput UpdateNoteInput
                ]
                []
            ]
        , div
            [ class "row" ]
            [ button
                [ class "btn"
                , class "btn-success"
                , class "m-1"
                , class "col"
                , onClick FinishScan
                , disabled <| not awaitingInteraction
                ]
                [ text "Finish Scan" ]
            ]
        ]


viewGuacamoleDisplay : Model -> Html Msg
viewGuacamoleDisplay model =
    let
        visibility =
            if model.scanState == Idle || model.scanState == ConnectingToBrowser then
                "hidden"

            else
                "visible"

        borderColor =
            if model.scanState == AwaitingInteraction then
                if model.guacamoleFocus then
                    "success"

                else
                    "info"

            else
                "warning"
    in
    div
        [ class "col-8"
        , class "p-0"
        , style "width" "max-content"
        ]
        [ div
            [ attribute "id" "display"
            , class "border"
            , class <| "border" ++ "-" ++ borderColor
            , class "border-3"
            , style "visibility" visibility
            , onMouseEnter (SetGuacamoleFocus True)
            , onMouseLeave (SetGuacamoleFocus False)
            ]
            []
        ]
