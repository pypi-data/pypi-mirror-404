from textual.app import App, ComposeResult
from textual.widgets import Static, Button, Header, Footer

from querycraft.SQL import *

class WindowDisplay(App):

    CSS = """
    Screen {
        layout: grid;
        grid-size: 29 10;
        grid-gutter: 0;
    }

    #resultat {
        tint: green 5%;
        color: #00CC00;
        column-span: 20;
        row-span: 10;
        overflow: hidden;
        text-overflow: ellipsis;
        text-wrap: nowrap;
        height: 100%;
    }

    #title {
        color: #00CC00;
        column-span: 9;
        row-span: 2;
        padding: 1 0;
        text-align: center;
        height: 100%;
        text-style: underline bold;
    }

    #link0, #link1, #link2, #link3, #link4, #link5, #link6 {
        color: #00CC00;
        width: 100%;
        height: 100%;
        column-span: 3;
        row-span: 2;
        padding: 1 1;

        text-align: center;
        overflow: hidden;
        text-overflow: ellipsis;
        text-wrap: nowrap;
        

    }

    Button {
        tint: white 15%;
        color: #00CC00;
        width: 100%;
        height: 100%;
        column-span: 3;
        row-span: 2;
        padding: 0;
        margin: 0;
    }
    """

    def __init__(self,tab):
        super().__init__()
        self.tab = tab
        
        for i, c in enumerate(self.tab):
            print(c.__str__())

    def compose(self) -> ComposeResult:
        yield Static("\n".join(str(item) for item in self.tab), id="resultat")   
        yield Static("QueryCraft\n", id="title")

        for i, item in enumerate(self.tab):
            yield Button(str(item), id=f"button{i}")
            yield Static("═══════════════\n║\n║\n║\n║\n║\n║", id=f"link{i}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        resultat = self.query_one("#resultat", Static)
        if event.button.id.startswith("button"):
            index = int(event.button.id.replace("button", ""))
            resultat.update(str(self.tab[index]._SQL__pl_data))