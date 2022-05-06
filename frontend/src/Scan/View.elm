module Scan.View exposing (viewDescription, viewDescriptionText, viewLog)

import Html exposing (Html, b, dd, div, dl, dt, li, text, ul)
import Html.Attributes exposing (class, style)
import List exposing (length)
import Scan.Data exposing (LogEntry, LogLevel(..))


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

            logText =
                if List.isEmpty log then
                    "no entries"

                else
                    String.fromInt (List.length log) ++ " entries"
        in
        div []
            [ viewDescriptionText "Log" logText
            , ul
                [ class "col"
                , class "mx-3"
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
