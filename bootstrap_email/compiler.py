import importlib.metadata
import os
import re
from importlib.resources import files
from string import Template

import cssutils
import sass
from cssselect import GenericTranslator
from lxml import etree
from lxml.html import (
    HtmlElement,
    HTMLParser,
    document_fromstring,
    fragment_fromstring,
    fragments_fromstring,
    tostring,
)
from premailer import transform

# XHTML doctype which ensures best compatibility in email clients
# https://github.com/bootstrap-email/bootstrap-email/discussions/168
EMAIL_COMPATIBILITY_DOCTYPE = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'


def compile(input_html: str) -> str:
    """Compile the given input HTML fragment into a complete HTML
    document that will render consistently across email clients."""

    document = compile_html(input_html)
    document = inline_css(document)
    document = configure_html(document)

    finalized = finalize_document(document)

    return finalized


def finalize_document(document: HtmlElement) -> str:
    html_ascii_bytes = tostring(
        document,
        encoding="US-ASCII",
        doctype=EMAIL_COMPATIBILITY_DOCTYPE,
        include_meta_content_type=True,
    )

    support_url_tokens(html_ascii_bytes)
    # ensure_doctype(html) # not necessary as we set it above
    # TODO: re-add the meta tag with the charset near the end... not sure how important
    # that is...

    return html_ascii_bytes.decode(encoding="US-ASCII")


def inline_css(document: HtmlElement) -> HtmlElement:
    html = tostring(document, encoding="unicode", include_meta_content_type=True)
    css = compile_scss("bootstrap-email.scss", "expanded")

    # TODO: possible speedup for bulk emails if you create an instance of
    # the Premailer class instead of calling transform() directly
    inlined_html = transform(html, css_text=css, disable_leftover_css=True)

    return document_fromstring(inlined_html)


def configure_html(document: HtmlElement):
    add_head_style(document)
    add_missing_meta_tags(document)
    add_version_comment(document)

    return document


def compile_html(input_html: str) -> HtmlElement:
    """Transform the structure of the given HTML fragment to ensure it will render
    consistently across email clients.

    Args:
        input_html (str): HTML fragment to compile

    Returns:
        HtmlElement: transformed HTML document
    """
    complete_html = template("base.html", {"contents": input_html})

    unicode_parser = HTMLParser(encoding="utf-8")
    document = document_fromstring(complete_html, parser=unicode_parser)

    convert_body(document)
    convert_block(document)

    convert_button(document)
    convert_badge(document)
    convert_alert(document)
    convert_card(document)
    convert_hr(document)
    convert_container(document)
    convert_grid(document)
    convert_stack(document)

    convert_color(document)
    convert_spacing(document)
    convert_margin(document)
    convert_spacer(document)
    convert_align(document)
    convert_padding(document)

    convert_preview(document)
    convert_table(document)

    return document


def convert_body(document: HtmlElement):
    body = document.find(".//body")
    classes = " ".join(s for s in [body.get("class", ""), "body"] if s)
    content = tostring(body, encoding="unicode")
    templated_body = template(
        "templates/body.html", {"contents": content, "classes": classes}
    )
    new_element = fragment_fromstring(templated_body)

    for child in body:
        body.remove(child)

    body.append(new_element)


def convert_block(document: HtmlElement):
    for node in document.cssselect("block, .to-table"):
        classes = node.get("class", "").split()
        if "to-table" not in classes:
            classes.append("to-table")
        classes = " ".join(classes)
        contents = inner_html(node)

        templated = template(
            "templates/table.html",
            {"contents": contents, "classes": classes},
        )
        new_element = fragment_fromstring(templated)

        node.getparent().replace(node, new_element)


def convert_button(document: HtmlElement):
    for node in document.cssselect(".btn"):
        classes = node.get("class", "")

        # remove the class attribute from the node
        node.attrib.pop("class", None)

        templated = template(
            "templates/table.html",
            {"contents": tostring(node, encoding="unicode"), "classes": classes},
        )
        new_element = fragment_fromstring(templated)

        node.getparent().replace(node, new_element)


def convert_badge(document: HtmlElement):
    for node in document.cssselect(".badge"):
        classes = node.get("class", "")

        # remove the class attribute from the node
        node.attrib.pop("class", None)

        templated = template(
            "templates/table-left.html",
            {"contents": tostring(node, encoding="unicode"), "classes": classes},
        )
        new_element = fragment_fromstring(templated)

        node.getparent().replace(node, new_element)


def convert_alert(document: HtmlElement):
    for node in document.cssselect(".alert"):
        classes = node.get("class", "")

        # remove the class attribute from the node
        node.attrib.pop("class", None)

        templated = template(
            "templates/table.html",
            {"contents": tostring(node, encoding="unicode"), "classes": classes},
        )
        new_element = fragment_fromstring(templated)

        node.getparent().replace(node, new_element)


def convert_card(document: HtmlElement):
    for node in document.cssselect(".card"):
        classes = node.get("class", "")

        # remove the class attribute from the node
        node.attrib.pop("class", None)

        inner_html = "".join([tostring(child, encoding="unicode") for child in node])
        templated = template(
            "templates/table.html",
            {"contents": inner_html, "classes": classes},
        )
        new_element = fragment_fromstring(templated)

        node.getparent().replace(node, new_element)

    for node in document.cssselect(".card-body"):
        classes = node.get("class", "")

        # remove the class attribute from the node
        node.attrib.pop("class", None)

        inner_html = "".join([tostring(child, encoding="unicode") for child in node])
        templated = template(
            "templates/table.html",
            {"contents": inner_html, "classes": classes},
        )
        new_element = fragment_fromstring(templated)

        node.getparent().replace(node, new_element)


def convert_hr(document: HtmlElement):
    for node in document.cssselect("hr"):
        default_margin_class = "" if has_vertical_margin_class(node) else "my-5"

        classes = " ".join(
            s for s in [default_margin_class, "hr", node.get("class", "")] if s
        )
        templated_body = template(
            "templates/table.html", {"contents": "", "classes": classes}
        )
        new_element = fragment_fromstring(templated_body)

        node.getparent().replace(node, new_element)


def convert_container(document: HtmlElement):
    for container in document.cssselect(".container"):
        classes = container.get("class")
        contents = inner_html(container)
        templated_body = template(
            "templates/container.html",
            {"contents": contents, "classes": classes},
        )
        new_element = fragment_fromstring(templated_body)
        container.getparent().replace(container, new_element)

    for fluid_container in document.cssselect(".container-fluid"):
        classes = fluid_container.get("class")
        contents = inner_html(fluid_container)
        templated_body = template(
            "templates/table.html",
            {"contents": contents, "classes": classes},
        )
        new_element = fragment_fromstring(templated_body)
        fluid_container.getparent().replace(fluid_container, new_element)


def convert_grid(document: HtmlElement):
    for node in document.cssselect(".row"):
        if node.xpath("./*[contains(@class, 'col-lg-')]"):
            class_name = node.get("class", "").split()
            if "row-responsive" not in class_name:
                class_name.append("row-responsive")
            node.set("class", " ".join(class_name))

        table_to_tr = template(
            "templates/table-to-tr.html",
            {"contents": inner_html(node), "classes": ""},
        )
        div = template(
            "templates/div.html",
            {"contents": table_to_tr, "classes": node.get("class", "")},
        )
        new_element = fragment_fromstring(div)

        node.getparent().replace(node, new_element)

    for node in document.xpath('//*[contains(@class, "col")]'):
        td = template(
            "templates/td.html",
            {"contents": inner_html(node), "classes": node.get("class", "")},
        )

        new_element = fragment_fromstring(td)

        node.getparent().replace(node, new_element)


def convert_stack(document: HtmlElement):
    for node in document.cssselect(".stack-row"):
        html = ""
        for child in node:
            html += template(
                "templates/td.html",
                {
                    "contents": tostring(child, encoding="unicode"),
                    "classes": "stack-cell",
                },
            )

        new_e_string = template(
            "templates/table-to-tr.html",
            {"contents": html, "classes": node.get("class", "")},
        )
        new_element = fragment_fromstring(new_e_string)

        node.getparent().replace(node, new_element)

    for node in document.cssselect(".stack-col"):
        html = ""
        for child in node:
            html += template(
                "templates/tr.html",
                {
                    "contents": tostring(child, encoding="unicode"),
                    "classes": "stack-cell",
                },
            )

        new_e_string = template(
            "templates/table-to-tbody.html",
            {"contents": html, "classes": node.get("class", "")},
        )
        new_element = fragment_fromstring(new_e_string)

        node.getparent().replace(node, new_element)


def convert_color(document: HtmlElement):
    for node in document.xpath('//*[contains(@class, "bg-")]'):
        # replace divs with tables as support for div background color
        # is spotty in email clients
        if node.tag == "div":
            classes = node.get("class", "")
            node.attrib.pop("class", None)

            templated = template(
                "templates/table.html",
                {"contents": inner_html(node), "classes": f"{classes} w-full"},
            )
            new_element = fragment_fromstring(templated)

            node.getparent().replace(node, new_element)


def convert_spacing(document: HtmlElement):
    for node in document.xpath('//*[contains(@class, "space-y-")]'):
        spacer = re.search(r"space-y-((lg-)?\d+)", node.get("class", "")).group(1)
        # get all direct children except the first
        for child in node.xpath(
            "./*[position() < last()] | ./tbody/tr/td/*[position() < last()]"
        ):
            if not has_margin_bottom_class(child):
                classes = " ".join(
                    s for s in [child.get("class", ""), f"mb-{spacer}"] if s
                )
                child.set("class", classes)


def convert_margin(document: HtmlElement):
    # TODO: this is the problem with the spacing-2 test...
    for node in reversed(
        document.xpath(
            "//*[contains(@class, 'my-') or contains(@class, 'mt-') or contains(@class, 'mb-') or contains(@class, ' my-') or contains(@class, ' mt-') or contains(@class, ' mb-')]"  # noqa: E501
        )
    ):
        top_class = re.search(r"m[ty]{1}-(lg-)?(\d+)", node.get("class", ""))
        bottom_class = re.search(r"m[by]{1}-(lg-)?(\d+)", node.get("class", ""))
        node.set(
            "class", re.sub(r"m[tby]{1}-(lg-)?\d+", "", node.get("class", "")).strip()
        )
        html = ""
        if top_class:
            html += template(
                "templates/div.html",
                {
                    "contents": "",
                    "classes": f"s-{re.sub(r'm[ty]{1}-', '', top_class.group())}",
                },
            )
        html += tostring(node, encoding="unicode")
        if bottom_class:
            html += template(
                "templates/div.html",
                {
                    "contents": "",
                    "classes": f"s-{re.sub(r'm[by]{1}-', '', bottom_class.group())}",
                },
            )

        parent = node.getparent()
        index = parent.index(node)

        # Convert the HTML string to a list of elements
        new_elements = fragments_fromstring(html)

        # Insert the new elements at the position of the old element
        for i, new_element in enumerate(new_elements):
            parent.insert(index + i, new_element)

        # Remove the old element
        parent.remove(node)


def convert_spacer(document: HtmlElement):
    for node in document.xpath('//*[contains(@class, "s-")]'):
        classes = " ".join(s for s in [node.get("class", ""), "w-full"] if s)
        node.getparent().replace(
            node,
            fragment_fromstring(
                template(
                    "templates/table.html",
                    {
                        "contents": "&nbsp;",
                        "classes": classes,
                    },
                )
            ),
        )


def convert_align(document: HtmlElement):
    for type in ["left", "center", "right"]:
        full_type = f"ax-{type}"
        for node in document.xpath(f'//*[contains(@class, "{full_type}")]'):
            if node.tag not in ["table", "td"]:
                node.set("class", node.get("class", "").replace(full_type, "").strip())
                new_element = fragment_fromstring(
                    template(
                        "templates/table.html",
                        {
                            "contents": tostring(node, encoding="unicode"),
                            "classes": full_type,
                        },
                    )
                )
                node.getparent().replace(node, new_element)
                new_element.set("align", type)
            else:
                node.set("align", type)


def convert_padding(document: HtmlElement):
    for node in document.xpath(
        "//*[starts-with(@class, 'p-') or starts-with(@class, 'pt-') or starts-with(@class, 'pr-') or starts-with(@class, 'pb-') or starts-with(@class, 'pl-') or starts-with(@class, 'px-') or starts-with(@class, 'py-') or contains(@class, ' p-') or contains(@class, ' pt-') or contains(@class, ' pr-') or contains(@class, ' pb-') or contains(@class, ' pl-') or contains(@class, ' px-') or contains(@class, ' py-')]"  # noqa: E501
    ):
        if node.tag not in ["table", "td", "a"]:
            padding_regex = re.compile(r"p[trblxy]?-(?:lg-)?\d+")
            classes = " ".join(padding_regex.findall(node.get("class", "")))
            node.set("class", padding_regex.sub("", node.get("class", "")).strip())
            node.getparent().replace(
                node,
                fragment_fromstring(
                    template(
                        "templates/table.html",
                        {
                            "contents": tostring(node, encoding="unicode"),
                            "classes": classes,
                        },
                    )
                ),
            )


def convert_preview(document: HtmlElement):
    preview_node = document.find(".//preview")

    if preview_node is None:
        return

    # apply spacing after the text max of 278 characters so it doesn't show body text
    preview_node.text += "&#847; &zwnj; &nbsp; " * max(278 - len(preview_node.text), 0)
    node = fragment_fromstring(
        template(
            "templates/div.html",
            {
                "contents": preview_node.text,
                "classes": "preview",
            },
        )
    )
    preview_node.getparent().remove(preview_node)

    body = document.find(".//body")
    body.insert(0, node)


def convert_table(document: HtmlElement):
    for node in document.xpath("//table"):
        node.set("border", "0")
        node.set("cellpadding", "0")
        node.set("cellspacing", "0")


def add_head_style(document: HtmlElement):
    head = document.find(".//head")
    head.append(fragment_fromstring(bootstrap_email_head(document)))


def bootstrap_email_head(document: HtmlElement):
    return f"""
        <style type="text/css">
            {purged_css_from_head(document)}
        </style>
    """


def css_to_xpath(selector):
    return GenericTranslator().css_to_xpath(selector)


def purged_css_from_head(document: HtmlElement):
    css = compile_scss("bootstrap-head.scss", "compressed")

    default, custom = css.split("/*! allow_purge_after */")
    custom = custom or ""

    # Parse the stylesheet
    stylesheet = cssutils.parseString(custom)

    # Iterate backwards over the rules in the stylesheet
    for i in reversed(range(len(stylesheet.cssRules))):
        rule = stylesheet.cssRules[i]
        if rule.type == rule.STYLE_RULE:
            # Get the selector text
            selector_text = rule.selectorText

            # Convert the CSS selector to an XPath expression
            xpath_expr = css_to_xpath(selector_text)

            # Check if the selector is present in the document
            if not document.xpath(xpath_expr):
                # If the selector is not present, remove the rule from the stylesheet
                stylesheet.deleteRule(i)
        elif rule.type == rule.MEDIA_RULE:
            # If the rule is a media rule, iterate backwards over the nested rules
            for j in reversed(range(len(rule.cssRules))):
                nested_rule = rule.cssRules[j]
                if nested_rule.type == nested_rule.STYLE_RULE:
                    # Get the selector text
                    selector_text = nested_rule.selectorText

                    # Convert the CSS selector to an XPath expression
                    xpath_expr = css_to_xpath(selector_text)

                    # Check if the selector is present in the document
                    if not document.xpath(xpath_expr):
                        # If the selector is not present, remove the nested rule
                        # from the media rule
                        rule.deleteRule(j)
            if len(rule.cssRules) == 0:
                # If the media rule has no more nested rules,
                # remove it from the stylesheet
                stylesheet.deleteRule(i)

    return default + stylesheet.cssText.decode("utf-8")


def add_missing_meta_tags(document: HtmlElement):
    META_TAGS = [
        {
            "query": 'meta[@http-equiv="x-ua-compatible"]',
            "code": '<meta http-equiv="x-ua-compatible" content="ie=edge">',
        },
        {
            "query": 'meta[@name="x-apple-disable-message-reformatting"]',
            "code": '<meta name="x-apple-disable-message-reformatting">',
        },
        {
            "query": 'meta[@name="viewport"]',
            "code": '<meta name="viewport" content="width=device-width, initial-scale=1">',  # noqa: E501
        },
        {
            "query": 'meta[@name="format-detection"]',
            "code": '<meta name="format-detection" content="telephone=no, date=no, address=no, email=no">',  # noqa: E501
        },
    ][::-1]  # Reverse the list

    head = document.find(".//head")
    for tag in META_TAGS:
        if not head.xpath(tag["query"]):
            head.insert(0, fragment_fromstring(tag["code"]))


def add_version_comment(document: HtmlElement):
    head = document.find(".//head")
    head.insert(
        0,
        etree.Comment(
            f" Compiled with Python Bootstrap Email version: {importlib.metadata.version('bootstrap-email')} "  # noqa: E501
        ),
    )


def support_url_tokens(document: HtmlElement):
    # TODO: not sure what the original function actually does, skip for now
    pass


# -------- utility functions --------


def inner_html(node: HtmlElement) -> str:
    return (node.text or "") + "".join(
        tostring(child, encoding="unicode") for child in node
    )


def compile_scss(file: str, output_style: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scss_file = os.path.join(current_dir, file)
    css = sass.compile(filename=scss_file, output_style=output_style)
    return css


def has_vertical_margin_class(node: HtmlElement) -> bool:
    top = has_margin_top_class(node)
    bottom = has_margin_bottom_class(node)

    return top or bottom


def has_margin_top_class(node: HtmlElement) -> bool:
    return bool(re.search(r"m[ty]{1}-(lg-)?\d+", node.get("class", "")))


def has_margin_bottom_class(node: HtmlElement) -> bool:
    return bool(re.search(r"m[by]{1}-(lg-)?\d+", node.get("class", "")))


def template(template_name: str, mapping: dict) -> str:
    """Expands a template with a mapping."""

    template = files("bootstrap_email").joinpath(template_name).read_text()
    return Template(template).substitute(mapping)
