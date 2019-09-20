module Login exposing (main)

import Browser
import Element exposing (Element)
import Html exposing (Html)


main =
    Browser.sandbox { init = init, update = update, view = viewHtml }

type alias Model =
    {}


init : Model
init =
    {}


type Msg
    = None

update : Msg -> Model -> Model
update msg model = model


viewHtml : Model -> Html Msg
viewHtml model = Element.layout [] (view model)


view : Model -> Element Msg
view model = Element.text "Hello, world!"
