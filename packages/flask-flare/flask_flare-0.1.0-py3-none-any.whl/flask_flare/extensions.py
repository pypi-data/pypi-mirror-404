from jinja2 import nodes
from jinja2.ext import Extension


class FlareExtension(Extension):
    tags = {"flarebutton", "flareselect"}

    def parse(self, parser):
        token = next(parser.stream)
        tag_name = token.value.replace("flare", "")  # 'button' or 'select'
        lineno = token.lineno

        body = parser.parse_statements(
            [f"name:endflare{tag_name}"],
            drop_needle=True,
        )

        return nodes.CallBlock(
            self.call_method(
                "_render",
                [nodes.Const(tag_name)],
            ),
            [],
            [],
            body,
        ).set_lineno(lineno)

    def _render(self, component, caller):
        template = f"{component}.html"
        return self.environment.get_template(template).render(
            content=caller()
        )
