module Scan.View exposing (viewDescription, viewDescriptionText, viewLog)

import Html exposing (Html, b, dd, div, dl, dt, li, text, ul)
import Html.Attributes exposing (class)
import Scan.Data exposing (LogEntry, LogLevel(..))
import Html.Attributes exposing (style)


viewLog : List LogEntry -> Html msg
viewLog log =
    if List.isEmpty log then
        text ""

    else
        let
            levelToString l =
                case l of
                    Info ->
                        "info"

                    Warning ->
                        "warning"

                    Error ->
                        "danger"

            viewLogEntry entry =
                li
                    [ class "list-group-item"
                    , class <| "list-group-item-" ++ levelToString entry.level
                    ]
                    [ text entry.msg ]
        in
        div []
            [ b [ class "mx-3" ] [ text "Log" ]
            , ul
                [ class "col"
                , class "m-3"
                , class "list-group"
                , style "max-height" "15em"
                , class "overflow-auto"
                ]
              <|
                List.map viewLogEntry log
            ]


viewDescriptionText : String -> String -> Html msg
viewDescriptionText description value =
    viewDescription
        description
        (if String.isEmpty value then
            Nothing

         else
            Just <| text value
        )


viewDescription : String -> Maybe (Html msg) -> Html msg
viewDescription description item =
    dl [ class "row", class "m-1" ]
        [ dt [ class "col-sm-3" ] [ text description ]
        , dd [ class "col-sm-9" ] [ item |> Maybe.withDefault (text "-") ]
        ]
