port module Scan.Page exposing (..)

import Html exposing (Html, button, div, h2, input, label, li, span, text, ul)
import Html.Attributes exposing (attribute, class, classList, style)
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
        , div [ class "row m-2" ]
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
        , ul [ class "list-group" ] <|
            List.map viewError model.errors
        , div [ class "row m-2", style "height" "1000px" ]
            [ div
                [ attribute "id" "display"
                , onMouseEnter (SetGuacamoleFocus True)
                , onMouseLeave (SetGuacamoleFocus False)
                , class "col"
                ]
                []
            ]
        ]


viewError : Data.ServerError -> Html Msg
viewError error =
    li
        [ classList
            [ ( "list-group-item", True )
            , ( "list-group-item-danger", True )
            ]
        ]
        [ text error.msg ]
