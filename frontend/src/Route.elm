module Route exposing (Route(..), modifyUrl, routeToString, toRoute)

import Ports
import Url
import Url.Parser as Url exposing ((</>), (<?>), Parser, oneOf, s)


type Route
    = NotFound
    | Scanner
    | Replay


routeToString : Route -> String
routeToString r =
    let
        parts =
            case r of
                NotFound ->
                    [ "err" ]

                Scanner ->
                    [ "scanner" ]

                Replay ->
                    [ "replay" ]
    in
    String.join "/" parts


modifyUrl : Route -> Cmd msg
modifyUrl =
    routeToString >> Ports.pushUrl


toRoute : String -> Route
toRoute string =
    case Url.fromString string of
        Nothing ->
            NotFound

        Just url ->
            Maybe.withDefault NotFound (Url.parse route url)


route : Parser (Route -> a) a
route =
    oneOf
        [ Url.map NotFound (s "err")
        , Url.map Scanner (s "scanner")
        , Url.map Replay (s "replay")
        ]
