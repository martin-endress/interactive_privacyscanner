port module Scan.Page exposing (..)

import Bytes exposing (Bytes)
import Delay
import Html exposing (Html, b, button, dd, div, dl, dt, h2, input, label, li, text, ul)
import Html.Attributes exposing (attribute, class, classList, disabled, style)
import Html.Events exposing (onClick, onInput, onMouseEnter, onMouseLeave)
import Http exposing (Metadata)
import Http.Detailed exposing (Error)
import Json.Decode as D
import Scan.Data as Data exposing (ContainerStartInfo, ScanStatus(..), ScanUpdate(..), ServerError)
import Scan.Requests as Requests



-- MODEL


type alias Model =
    { status : ScanStatus
    , connection : Maybe Connection
    , interactionCount : Int
    , urlInput : String
    , guacamoleFocus : Bool
    , errors : List ServerError
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
    | GotStartResult (Result (Error String) ( Metadata, ContainerStartInfo ))
    | ConnectToGuacamole
    | ReceiveScanUpdate ScanUpdate
    | RegisterInteraction
    | GotRegisterInteraction (Result (Error Bytes) ())



-- PORTS


port connectTunnel : Int -> Cmd msg


port setGuacamoleFocus : Bool -> Cmd msg


port messageReceiver : (D.Value -> msg) -> Sub msg



-- INIT


init : Model
init =
    { status = Idle
    , connection = Nothing
    , interactionCount = 0
    , urlInput = ""
    , guacamoleFocus = False
    , errors = []
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
            ( { model
                | status = ConnectingToBrowser
              }
            , Requests.startScan GotStartResult model.urlInput
            )

        GotStartResult result ->
            processStartResult model result

        ConnectToGuacamole ->
            ( model
            , model.connection
                |> Maybe.map .vncPort
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
                |> Maybe.map (Requests.registerUserInteraction GotRegisterInteraction)
                |> Maybe.withDefault Cmd.none
            )

        GotRegisterInteraction result ->
            ( processRegisterInteractionResult result model
            , Cmd.none
            )


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
            ( { model
                | status = InitialScanInProgress
                , connection = Just connection
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
    case scanUpdate of
        NoOp ->
            model

        ScanComplete ->
            updateStatus AwaitingInteraction model

        GuacamoleError message ->
            { model
                | errors = { msg = message } :: model.errors
            }

        URLChanged _ ->
            -- todo
            model


processRegisterInteractionResult : Result (Error Bytes) () -> Model -> Model
processRegisterInteractionResult result =
    case result of
        Ok _ ->
            updateStatus ScanInProgress

        Err error ->
            appendError error


updateStatus : ScanStatus -> Model -> Model
updateStatus newStatus model =
    { model | status = newStatus }


appendError : Error a -> Model -> Model
appendError error model =
    { model
        | errors = Data.errorFromResponse error :: model.errors
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
        [ h2 [] [ text "Interactive Privacy Scanner" ]
        , viewStartInput model
        , div [ class "row m-2", style "height" "1000px" ]
            [ viewGuacamoleDisplay model.guacamoleFocus
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


viewGuacamoleDisplay : Bool -> Html Msg
viewGuacamoleDisplay inFocus =
    div
        [ attribute "id" "display"
        , classList
            [ ( "col", True )
            , ( "border", inFocus )
            , ( "border-success", inFocus )
            , ( "border-2", inFocus )
            ]
        , onMouseEnter (SetGuacamoleFocus True)
        , onMouseLeave (SetGuacamoleFocus False)
        ]
        []


viewStatusPanel : Model -> Html Msg
viewStatusPanel model =
    let
        awaitingInteraction =
            model.status == AwaitingInteraction
    in
    div
        [ class "col-md-4", class "bg-light" ]
        [ descriptionList
            [ ( "Status", Data.statusToString model.status )
            , ( "Current URL", "." )
            , ( "Interactions", String.fromInt model.interactionCount )
            ]
        , viewErrors model.errors
        , div
            [ class "row", class "m-2" ]
            [ button
                [ class "btn"
                , class "btn-primary"
                , onClick RegisterInteraction

                --, disabled <| not awaitingInteraction
                ]
                [ text "Register User Interaction" ]
            ]
        , div [ class "row", class "m-2" ]
            [ button
                [ class "btn"
                , class "btn-success"
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
    div
        [ class "row", class "m-2" ]
        [ div [ class "col-sm-3" ] [ b [] [ text "Errors" ] ]
        , if List.isEmpty serverErrors then
            div [ class "col-sm-9" ] [ text "no errors :)" ]

          else
            ul [ class "col", class "list-group" ] <|
                List.map viewError serverErrors
        ]


viewError : Data.ServerError -> Html Msg
viewError error =
    li [ class "list-group-item-danger" ] [ text error.msg ]
