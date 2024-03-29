module Results.Page exposing (..)

import Html exposing (Html, button, div, h2, text)
import Html.Attributes exposing (attribute, class, id, style, type_)
import Html.Events exposing (onClick)
import Http exposing (Metadata)
import Http.Detailed exposing (Error)
import Results.Data exposing (ScanInfo)
import Results.Requests as Requests



-- MODEL


type alias Model =
    { scanList : List ScanInfo

    --, currentScanSelection : Maybe ScanDetails
    }


type Msg
    = GetScanList
    | GotScanList (Result (Error String) ( Metadata, List ScanInfo ))
    | ViewScanner
    | ReplayScan String
    | GotReplayScan (Result (Error String) ( Metadata, Int ))
    | DownloadResult String
    | DownloadAllResults



-- INIT


init : Model
init =
    { scanList = []
    }



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        GetScanList ->
            ( model, Requests.getAllScans GotScanList )

        GotScanList scansInfo ->
            case scansInfo of
                Ok ( _, scanList ) ->
                    ( { model | scanList = scanList }
                    , Cmd.none
                    )

                Err _ ->
                    ( model, Cmd.none )

        ReplayScan scanId ->
            ( model, Requests.replayScan GotReplayScan scanId )

        GotReplayScan response ->
            case response of
                Ok ( _, _ ) ->
                    ( model
                    , Cmd.none
                    )

                Err _ ->
                    ( model, Cmd.none )

        DownloadResult scanId ->
            ( model, Requests.downloadResult scanId )

        DownloadAllResults ->
            ( model, Requests.downloadAllResults )

        ViewScanner ->
            -- handled in Main
            ( model, Cmd.none )



-- VIEW


view : Model -> Html Msg
view model =
    div
        [ class "container-fluid" ]
        [ div [ class "row", class "justify-content-center" ]
            [ viewStatusPanel model
            , viewResultPanel model
            ]
        ]


viewStatusPanel : Model -> Html Msg
viewStatusPanel model =
    div
        [ class "col-4"
        , class "p-3"
        , class "bg-light"
        , class "vh-100"
        , class "d-flex"
        , class "flex-column"
        ]
        [ div [ class "row" ]
            [ div
                [ class "col" ]
                [ text <| "#Scans:" ++ String.fromInt (List.length model.scanList) ]
            , div [ class "col" ]
                [ button
                    [ class "btn"
                    , class "btn-primary"
                    , class "btn-sm"
                    , onClick DownloadAllResults
                    ]
                    [ text "Download All Results" ]
                ]
            , div
                [ class "col" ]
                [ button
                    [ class "btn"
                    , class "btn-secondary"
                    , class "float-end"
                    , class "btn-sm"
                    , onClick GetScanList
                    ]
                    [ text "🗘"
                    ]
                ]
            ]
        , div
            [ class "row"
            , class "overflow-auto"
            , class "py-2"
            , style "max-height" "50%"
            ]
            [ viewResultList model.scanList ]
        , div
            [ class "row"
            , class "justify-content-center"
            , class "flex-grow-1"
            ]
            []
        , div
            [ class "container", class "m-1" ]
            [ div
                [ class "row" ]
                [ button
                    [ class "btn"
                    , class "btn-success"
                    , class "m-1"
                    , class "col"
                    , onClick ViewScanner
                    ]
                    [ text "View Scanner" ]
                ]
            ]
        ]


viewResultList : List ScanInfo -> Html Msg
viewResultList scans =
    div
        [ class "accordion"
        , id "resultAccordion"
        , class "w-100"
        ]
        (scans
            |> List.indexedMap Tuple.pair
            |> List.map viewResultEntry
        )


viewResultEntry : ( Int, ScanInfo ) -> Html Msg
viewResultEntry ( cssNumber, scan ) =
    let
        headingId =
            "heading" ++ String.fromInt cssNumber

        collapseId =
            "collapse" ++ String.fromInt cssNumber
    in
    div
        [ class "accordion-item", class "p-0" ]
        [ h2
            [ class "accordion-header", id headingId ]
            [ button
                [ class "accordion-button"
                , class "collapsed"
                , type_ "button"
                , attribute "data-bs-toggle" "collapse"
                , attribute "data-bs-target" ("#" ++ collapseId)
                , attribute "aria-expanded" "false"
                , attribute "aria-controls" collapseId
                ]
                [ text scan.id ]
            ]
        , div
            [ id collapseId
            , class "accordion-collapse"
            , class "collapse"
            , attribute "aria-labelledby" headingId
            , attribute "data-bs-parent" "resultAccordion"
            ]
            [ viewResultEntryBody scan
            ]
        ]


viewResultEntryBody : ScanInfo -> Html Msg
viewResultEntryBody scan =
    div
        [ class "accordion-body", class "container" ]
        [ div [ class "row" ]
            (viewScanEntry "first scan" scan.initialScan.success
                :: (scan.replays
                        |> List.map (\s -> viewScanEntry "recorded scan" s.success)
                   )
            )
        , div [ class "row", class "m-2", class "p-2" ]
            [ button
                [ class "col"
                , class "btn"
                , class "m-1"
                , class "btn-primary"
                , class "btn-sm"
                , onClick (ReplayScan scan.id)
                ]
                [ text "Replay recorded scan" ]
            , button
                [ class "col"
                , class "btn"
                , class "m-1"
                , class "btn-primary"
                , class "btn-sm"
                , onClick (DownloadResult scan.id)
                ]
                [ text "Download Scan" ]
            ]
        ]


viewScanEntry : String -> Bool -> Html Msg
viewScanEntry name success =
    let
        successSymbol =
            if success then
                "✓"

            else
                "✕"
    in
    div
        [ class "row", class "m-2" ]
        [ div [ class "col" ] [ text name ]
        , div [ class "col" ] [ text successSymbol ]
        , button
            [ class "col"
            , class "btn"
            , class "btn-light"
            , class "float-end"
            , class "btn-sm"
            ]
            [ text "Show Result (WIP)" ]
        ]


viewResultPanel : Model -> Html Msg
viewResultPanel _ =
    div
        [ class "col-8"
        , class "p-0"
        ]
        []
