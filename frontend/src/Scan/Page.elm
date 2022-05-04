port module Scan.Page exposing (..)

import Bytes exposing (Bytes)
import Delay
import Html exposing (Html, b, button, dd, div, dl, dt, h2, h4, input, label, li, text, ul)
import Html.Attributes exposing (attribute, class, classList, disabled, style)
import Html.Events exposing (onClick, onInput, onMouseEnter, onMouseLeave)
import Http exposing (Metadata)
import Http.Detailed exposing (Error)
import Json.Decode as D
import Json.Encode as E
import Maybe exposing (withDefault)
import Scan.Data as Data exposing (ContainerStartInfo, LogEntry, ScanState(..), ScanUpdate(..), scanUpdateToString)
import Scan.Requests as Requests
import Scan.View as View



-- MODEL


type alias Model =
    { scanState : ScanState
    , connection : Maybe Connection
    , interactionCount : Int
    , urlInput : String
    , currentUrl : String
    , guacamoleFocus : Bool
    , log : List LogEntry
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
    , log = sampleLog
    }


sampleLog =
    [ { msg = "Info log message", level = Data.Info }
    , { msg = "Warning log message", level = Data.Warning }
    , { msg = "Error log message", level = Data.Error }
    , { msg = "asdfLong message:  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus mollis venenatis augue vehicula tristique. Integer felis ante, consectetur id mi eu, efficitur luctus lorem. Quisque risus lorem, vulputate eu imperdiet sed, tincidunt commodo justo. Cras tincidunt lacus ligula, pretium sollicitudin tortor congue a. Phasellus id convallis leo. Vivamus quis tincidunt lectus. Pellentesque commodo, urna sit amet vulputate fringilla, risus lacus vulputate odio, eget aliquet mauris diam eu metus. Vivamus auctor sit amet justo eu placerat. Donec mi diam, egestas ac mi et, pharetra convallis lectus. Nulla ultrices libero id leo blandit, nec luctus magna feugiat. "
      , level = Data.Error
      }
    , { msg = "asdfLong message:  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus mollis venenatis augue vehicula tristique. Integer felis ante, consectetur id mi eu, efficitur luctus lorem. Quisque risus lorem, vulputate eu imperdiet sed, tincidunt commodo justo. Cras tincidunt lacus ligula, pretium sollicitudin tortor congue a. Phasellus id convallis leo. Vivamus quis tincidunt lectus. Pellentesque commodo, urna sit amet vulputate fringilla, risus lacus vulputate odio, eget aliquet mauris diam eu metus. Vivamus auctor sit amet justo eu placerat. Donec mi diam, egestas ac mi et, pharetra convallis lectus. Nulla ultrices libero id leo blandit, nec luctus magna feugiat "
      , level = Data.Error
      }
    ]



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
                | log = Data.errorFromStringResponse error :: model.log
              }
            , Cmd.none
            )


processScanUpdate : ScanUpdate -> Model -> Model
processScanUpdate scanUpdate model =
    case ( scanUpdate, model.scanState ) of
        ( NoOp, _ ) ->
            model

        ( ScanComplete, ScanInProgress ) ->
            updateScanState
                AwaitingInteraction
                { model | interactionCount = model.interactionCount + 1 }

        ( ScanComplete, FinalScanInProgress ) ->
            init

        ( SocketError message, _ ) ->
            appendLogEntry
                { msg = "VNC error:" ++ message, level = Data.Error }
                model

        ( GuacamoleError message, _ ) ->
            appendLogEntry
                { msg = "Guacamole error:" ++ message, level = Data.Error }
                model

        ( Log message, _ ) ->
            let
                entry =
                    { msg = message, level = Data.Info }
            in
            appendLogEntry entry model

        ( URLChanged newUrl, _ ) ->
            -- todo
            { model | currentUrl = newUrl }

        ( _, _ ) ->
            -- Illegal state
            appendLogEntry
                { msg =
                    "Illegal State. (msg="
                        ++ scanUpdateToString scanUpdate
                        ++ ", state="
                        ++ Data.stateToString model.scanState
                        ++ ")"
                , level = Data.Error
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
    messageReceiver Data.mapScanUpdated
        |> Sub.map ReceiveScanUpdate



-- VIEW


view : Model -> Html Msg
view model =
    div
        [ class "container-fluid" ]
        [ div [ class "row" ]
            [ viewStatusPanel model
            , viewGuacamoleDisplay model
            ]
        ]


viewStatusPanel : Model -> Html Msg
viewStatusPanel model =
    div
        [ class "col"
        , class "col-md-4"
        , class "bg-light"
        , class "vh-100"
        ]
        [ h4 [ class "m-3", class "text-center" ] [ text "Interactive Privacyscanner" ]
        , viewStartInput model
        , View.viewDescriptionText "Status" <| Data.stateToString model.scanState
        , View.viewDescriptionText "Current URL" model.currentUrl
        , View.viewDescriptionText "Interactions" <| String.fromInt model.interactionCount
        , viewButtons (model.scanState == AwaitingInteraction)
        , View.viewLog model.log
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


viewButtons : Bool -> Html Msg
viewButtons awaitingInteraction =
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
                , onClick RegisterInteraction
                , disabled <| not awaitingInteraction
                ]
                [ text "Register User Interaction" ]
            ]
        , div
            [ class "row" ]
            [ button
                [ class "btn"
                , class "btn-success"
                , class "m-1"
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
