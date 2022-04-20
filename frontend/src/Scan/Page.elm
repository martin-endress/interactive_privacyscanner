port module Scan.Page exposing (..)

import Html exposing (Html, button, div, h2, input, label, span, text)
import Html.Attributes exposing (attribute, class, style)
import Html.Events exposing (onClick, onInput, onMouseEnter, onMouseLeave)
import Http
import Scan.Data exposing (ContainerStartInfo)
import Scan.Requests as Requests


type alias Model =
    { status : Bool -- status represents the scanning status
    , urlInput : String
    , guacamoleFocus : Bool
    , guacamoleErrors : List String
    }


type Msg
    = Empty
    | UpdateUrlInput String
    | StartScan
    | ReceiveGuacamoleError String
    | SetGuacamoleFocus Bool
    | GotStartResult (Result Http.Error ContainerStartInfo)



-- PORTS


port connectTunnel : Int -> Cmd msg


port setGuacamoleFocus : Bool -> Cmd msg


port messageReceiver : (String -> msg) -> Sub msg



-- INIT


init : Model
init =
    { status = False
    , urlInput = ""
    , guacamoleFocus = False
    , guacamoleErrors = []
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
            in
            ( model, startContainer )

        ReceiveGuacamoleError guacamoleMessage ->
            let
                _ =
                    Debug.log "GUACAMOLE ERROR" guacamoleMessage
            in
            ( { model
                | guacamoleErrors = guacamoleMessage :: model.guacamoleErrors
              }
            , Cmd.none
            )

        SetGuacamoleFocus val ->
            ( { model | guacamoleFocus = val }
            , setGuacamoleFocus val
            )

        GotStartResult result ->
            let
                _ =
                    Debug.log "got result" result
            in
            case result of
                Ok containerInfo ->
                    ( model, Cmd.none )

                Err error ->
                    ( model, Cmd.none )


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
