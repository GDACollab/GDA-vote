module Login exposing (main)

import Browser
import Element exposing (Element, column, row, text)
import Element.Input
import Html exposing (Html)


main =
    Browser.sandbox { init = init, update = update, view = (Element.layout []) << view }


type alias Model =
    { login : LoginForm
    }

type alias LoginForm =
    { username : String
    , password : String
    }

init : Model
init =
    { login = { username = "", password = "" }
    }


type LoginUpdateMsg
    = SetUsername String
    | SetPassword String
    | ClearLogin


type Msg
    = LoginUpdate LoginUpdateMsg
    | SubmitLogin


updateLogin : LoginUpdateMsg -> LoginForm -> LoginForm
updateLogin msg login =
    case msg of
        SetUsername username ->
            { login | username = username }

        SetPassword password ->
            { login | password = password }

        ClearLogin ->
            { username = "", password = "" }


update : Msg -> Model -> Model
update msg model =
    case msg of
        LoginUpdate m ->
            { model | login = updateLogin m model.login }

        SubmitLogin ->
            model


viewHtml : Model -> Html Msg
viewHtml model =
    Element.layout [] (view model)


label msg =
    Element.Input.labelLeft [] (text msg)


viewUsername : String -> Element Msg
viewUsername username =
    Element.Input.username []
        { onChange = LoginUpdate << SetUsername
        , placeholder = Nothing
        , text = username
        , label = Element.Input.labelHidden "username"
        }


viewPassword : String -> Element Msg
viewPassword password =
    let
        params =
            { onChange = LoginUpdate << SetPassword
            , text = password
            , placeholder = Nothing
            , label = Element.Input.labelHidden "password"
            , show = False
            }
    in
    if password == "" then
        Element.Input.newPassword [] params

    else
        Element.Input.currentPassword [] params


fill =
    [ Element.width Element.fill
    , Element.height Element.fill
    ]


fillCenter =
    [ Element.centerX
    , Element.height Element.fill 
    ]

viewUsernamePasswordSignIn : LoginForm -> Element Msg
viewUsernamePasswordSignIn { username, password } =
    column fill
        [ row fill 
            [ Element.el [ Element.width (Element.px 100) ] (text "email: ")
            , viewUsername username 
            ]
        , row fill 
            [ Element.el [ Element.width (Element.px 100) ] (text "password: ")
            , viewPassword password 
            ]
        ]

viewLoginForm : LoginForm -> Element Msg
viewLoginForm login =
    Element.el
        [ Element.width (Element.minimum 200 (Element.fill))

        -- , Element.height (Element.px 600)
        , Element.centerX
        , Element.centerY
        ]
        (column fillCenter
            [ row fillCenter [ text "Welcome to GDA-Vote!" ]
            , row fillCenter [ text "Please sign in" ]
            , row [ Element.height (Element.px 20) ] []
            , row fill
                [ viewUsernamePasswordSignIn login ]
            ]
        )


view : Model -> Element Msg
view model =
    viewLoginForm model.login
