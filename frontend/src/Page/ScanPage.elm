module Page.ScanPage exposing (..)

import Html exposing (Html, button, div, h2, input, label, span, text)
import Html.Attributes exposing (attribute, class, style)
import Html.Events exposing (onClick, onInput)


type alias Model =
    { urlInput : String
    }


type Msg
    = Empty
    | UpdateUrlInput String
    | StartScan


init : Model
init =
    { urlInput = "" }


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    let
        a =
            Debug.log "" model.urlInput
    in
    case msg of
        Empty ->
            ( model, Cmd.none )

        UpdateUrlInput newUrl ->
            ( { model | urlInput = newUrl }, Cmd.none )

        StartScan ->
            ( model, Cmd.none )


view : Model -> Html Msg
view model =
    div
        [ class "container-fluid" ]
        [ h2 [] [ text "Interactive Privacy Scanner" ]
        , div [ class "row m-2" ]
            [ div [ class "col-md-6 mx-auto" ]
                [ label [ attribute "for" "url_input" ] [ text "Enter URL to perform an interactive scan:" ]
                , div [ class "input-group mb-3" ]
                    [ div [ class "input-group-prepend" ]
                        [ span [ class "input-group-text", attribute "id" "basic-addon3" ] [ text "http://" ]
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
            [ div [ attribute "id" "display", class "col" ] []
            ]
        ]
