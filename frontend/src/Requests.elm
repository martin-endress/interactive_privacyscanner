module Requests exposing (managerApi)


managerApi : String -> String
managerApi path =
    "http://scanner.psi.test/api/" ++ path
