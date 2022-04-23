port module Scan.Page exposing (..)

import Bytes exposing (Bytes)
import Html exposing (Html, b, button, dd, div, dl, dt, h2, input, label, li, text, ul)
import Html.Attributes exposing (attribute, class, classList, disabled, style)
import Html.Events exposing (onClick, onInput, onMouseEnter, onMouseLeave)
import Http exposing (Metadata)
import Http.Detailed exposing (Error)
import Scan.Data as Data exposing (ContainerStartInfo, ScanStatus(..), ServerError)
import Scan.Requests as Requests



-- MODEL


type alias Model =
    { status : ScanStatus
    , interactionCount : Int
    , urlInput : String
    , guacamoleFocus : Bool
    , errors : List ServerError
    }


type Msg
    = Empty
    | UpdateUrlInput String
    | SetGuacamoleFocus Bool
    | StartScan
    | GotStartResult (Result (Error String) ( Metadata, ContainerStartInfo ))
    | ReceiveGuacamoleError String
    | RegisterInteraction
    | GotRegisterInteraction (Result (Error Bytes) ())



-- PORTS


port connectTunnel : Int -> Cmd msg


port setGuacamoleFocus : Bool -> Cmd msg


port messageReceiver : (String -> msg) -> Sub msg



-- INIT


init : Model
init =
    { status = Idle
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
                | status = StartingContainer model.urlInput
              }
            , Requests.startContainerInstance GotStartResult model.urlInput
            )

        GotStartResult result ->
            processStartResult model result

        ReceiveGuacamoleError guacamoleMessage ->
            ( { model
                | errors =
                    { msg = guacamoleMessage
                    }
                        :: model.errors
              }
            , Cmd.none
            )

        RegisterInteraction ->
            ( model
            , Requests.registerUserInteraction GotRegisterInteraction ""
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
                ( newModel, vncPort ) =
                    ( { model | status = Connecting containerInfo }
                    , containerInfo.vnc_port
                    )
            in
            ( newModel
            , connectTunnel vncPort
            )

        Err error ->
            ( { model
                | errors = Data.errorFromStringResponse error :: model.errors
              }
            , Cmd.none
            )


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
    messageReceiver ReceiveGuacamoleError



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
    div
        [ class "col-md-4", class "bg-light" ]
        [ descriptionList
            [ ( "Status", Data.statusToString model.status )
            , ( "Current URL", "." )
            , ( "Interactions", String.fromInt model.interactionCount )
            ]
        , viewErrors model.errors

        -- progress bar
        --<div class="row m-1">
        --    <div class="progress container-fluid">
        --        <div id="scan_progress" class="progress-bar progress-bar-striped progress-bar-animated"
        --            role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0"
        --            aria-valuemax="100"></div>
        --    </div>
        --</div>
        , div
            [ class "row", class "m-2" ]
            [ button [ class "btn", class "btn-primary", disabled True ] [ text "Register User Interaction" ]
            ]
        , div [ class "row", class "m-2" ]
            [ button [ class "btn", class "btn-success", disabled True ] [ text "Finish Scan" ]
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
