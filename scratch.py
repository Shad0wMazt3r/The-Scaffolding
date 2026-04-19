import sys
import os

from pyratatui import (
    Block, Color, Constraint, Direction, Layout, Paragraph, Style, Table, Row, Terminal, prompt_text
)

def main():
    table_rows = [Row.from_strings(["hello", "world"])]
    header = Row.from_strings(["COL1", "COL2"]).style(Style().fg(Color.cyan()).bold())

    with Terminal() as term:
        while True:
            def ui(frame):
                frame.render_widget(Paragraph.from_string("Press 'a' to add, 'q' to quit"), frame.area)

            term.draw(ui)
            ev = term.poll_event(100)
            if ev:
                if ev.code == "q":
                    break
                elif ev.code == "a":
                    # Break out of loop to ask input or we can do it inside?
                    pass
    print("Done")

if __name__ == "__main__":
    main()
