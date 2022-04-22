port module Scan.Page exposing (..)

import Html exposing (Html, b, button, dd, div, dl, dt, h2, input, label, li, p, span, text, ul)
import Html.Attributes exposing (attribute, class, classList, disabled, style)
import Html.Events exposing (onClick, onInput, onMouseEnter, onMouseLeave)
import Http exposing (Metadata)
import Http.Detailed exposing (Error)
import Scan.Data as Data exposing (ContainerStartInfo, ScanStatus(..), ServerError)
import Scan.Requests as Requests


type alias Model =
    { status : ScanStatus
    , urlInput : String
    , guacamoleFocus : Bool
    , errors : List ServerError
    }


type Msg
    = Empty
    | UpdateUrlInput String
    | StartScan
    | ReceiveGuacamoleError String
    | SetGuacamoleFocus Bool
    | GotStartResult (Result (Error String) ( Metadata, ContainerStartInfo ))



-- PORTS


port connectTunnel : Int -> Cmd msg


port setGuacamoleFocus : Bool -> Cmd msg


port messageReceiver : (String -> msg) -> Sub msg



-- INIT


init : Model
init =
    { status = Idle
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

        StartScan ->
            let
                startContainer =
                    Requests.startContainerInstance GotStartResult model.urlInput

                newModel =
                    { model
                        | status = StartingContainer model.urlInput
                    }
            in
            ( newModel
            , startContainer
            )

        ReceiveGuacamoleError guacamoleMessage ->
            ( { model
                | errors =
                    { msg = guacamoleMessage
                    }
                        :: model.errors
              }
            , Cmd.none
            )

        SetGuacamoleFocus val ->
            ( { model | guacamoleFocus = val }
            , setGuacamoleFocus val
            )

        GotStartResult result ->
            case result of
                Ok ( _, containerInfo ) ->
                    let
                        ( newModel, vncPort ) =
                            updateStartContainer containerInfo model
                    in
                    ( newModel
                    , connectTunnel vncPort
                    )

                Err error ->
                    ( { model
                        | errors = Data.errorFromResponse error :: model.errors
                      }
                    , Cmd.none
                    )


updateStartContainer : ContainerStartInfo -> Model -> ( Model, Int )
updateStartContainer startInfo model =
    ( { model | status = Connecting startInfo }
    , startInfo.vnc_port
    )


messageSubscription : Sub Msg
messageSubscription =
    messageReceiver ReceiveGuacamoleError


view : Model -> Html Msg
view model =
    div
        [ class "container-fluid" ]
        [ h2 [] [ text "Interactive Privacy Scanner" ]
        , viewStartInput model
        , div [ class "row m-2", style "height" "1000px" ]
            [ viewGuacamoleDisplay
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
                [ div [ class "input-group-prepend" ]
                    [ span
                        [ class "input-group-text", attribute "id" "basic-addon3" ]
                        [ text "http://" ]
                    ]
                , input
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


viewGuacamoleDisplay : Html Msg
viewGuacamoleDisplay =
    div
        [ attribute "id" "display"
        , onMouseEnter (SetGuacamoleFocus True)
        , onMouseLeave (SetGuacamoleFocus False)
        , class "col"
        ]
        []


viewStatusPanel : Model -> Html Msg
viewStatusPanel model =
    div
        [ class "col-md-4", class "bg-light" ]
        [ descriptionList
            [ ( "Status", Data.statusToString model.status )
            , ( "Current URL", "" )
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
