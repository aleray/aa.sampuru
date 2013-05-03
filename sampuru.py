#! /usr/bin/env python


# Sampuru, an html baker.
# Copyright (C) 2013 Alexandre Leray

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import requests
import html5lib
import urlparse
import tinycss
import cssselect


# TODO:
# - @import rules
# - @medeia rules
# - !important flags
# - ::pseudo-elements
# - remove scripts tags? comments?
# - fetching stylesheets into style tags
# - inlining other assets: js, img, fonts etc.
# - testing


class HTMLBaker(object):
    html_parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("lxml"), namespaceHTMLElements=False)
    css_parser = tinycss.make_parser('page3')

    def __init__(self, url, xpath=None):
        self.url = url
        self.xpath = xpath
        self.tree = None
        self.req = None
        self.style_elts = []
        self.rules = []
        self.nodes = {}

    def remove_style_elts(self):
        """
        Removes any style-related node
        """
        for elt in self.tree.xpath('//link[@rel="stylesheet"]|//style'):
            elt.getparent().remove(elt)

    def absolutize_urls(self):
        """
        Makes absolute any reference to external resources.
        """
        for node in self.tree.xpath('//*[@href]'):
            href = node.get('href')
            absolute_href = urlparse.urljoin(self.req.url, href)
            node.set('href', absolute_href)

        for node in self.tree.xpath('//*[@src]'):
            src = node.get('src')
            absolute_src = urlparse.urljoin(self.req.url, src)
            node.set('src', absolute_src)

    def collect_styles(self):
        for elt in self.tree.xpath('//link[@rel="stylesheet"]|//style'):
            if elt.tag == "link":
                attr = elt.get('media', 'all')
                media = [m.strip() for m in attr.split(",")]
                if not ("all" in media or "screen" in media):
                    continue
            self.style_elts.append(elt)

    def collect_css_rules(self):
        for elt in self.style_elts:
            # parses the css rules
            if elt.tag == "link":
                url = elt.get('href')
                r = requests.get(url)
                parsed = HTMLBaker.css_parser.parse_stylesheet(r.text)
            else:
                parsed = HTMLBaker.css_parser.parse_stylesheet(elt.text, encoding=r.encoding)

            self.rules.extend(parsed.rules)

    def collect_for_nodes(self):
        for ruleset in self.rules:
            try:
                selectors = cssselect.parse(ruleset.selector.as_css())
            except:
                continue

            for selector in selectors:
                try:
                    xpath = cssselect.HTMLTranslator().selector_to_xpath(selector)
                except cssselect.xpath.ExpressionError:
                    continue

                # constructs a dictionnary for each node addressed by css, and
                # collects the associated declarations and priorities
                for node in self.tree.xpath(xpath):
                    if node not in self.nodes:
                        self.nodes[node] = {}

                    for declaration in ruleset.declarations:
                        # replaces if priority is equal of higher and if not important
                        new_specificity = selector.specificity()

                        if declaration.name in self.nodes[node]:
                            if self.nodes[node][declaration.name][1] > new_specificity:
                                continue

                        self.nodes[node][declaration.name] = (declaration.value.as_css(), selector.specificity())

                    style_attr = node.get('style')
                    if style_attr:
                        declarations = HTMLBaker.css_parser.parse_style_attr(style_attr)[0]
                        for declaration in declarations:
                            self.nodes[node][declaration.name] = (declaration.value.as_css(), (1, 0, 0, 0))

    def apply_css_rules(self):
        for node in self.nodes:
            style = "; ".join(["%s: %s" % (i[0], i[1][0]) for i in self.nodes[node].items()])
            node.set("style", style)

    def write(self, outfile):
        output = ""
        if self.xpath:
            p = self.tree.xpath(self.xpath)
            if p:
                output = "\n".join(html5lib.serialize(elt, tree="lxml", encoding="utf-8") for elt in p)
        else:
            output = html5lib.serialize(self.tree, tree="lxml", encoding="utf-8")

        open(outfile, 'wb').write(output)

    def run(self):
        self.req = requests.get(self.url)
        self.tree = HTMLBaker.html_parser.parse(self.req.text, encoding=self.req.encoding, parseMeta=True, useChardet=True)

        self.absolutize_urls()
        self.collect_styles()
        self.collect_css_rules()
        self.collect_for_nodes()
        self.apply_css_rules()
        self.remove_style_elts()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('url', help='The URL to scrap')
    parser.add_argument('destination', help='The destination to save the baked page')
    parser.add_argument('--xpath', help='xpath')

    args = parser.parse_args()

    baked = HTMLBaker(args.url, xpath=args.xpath)
    baked.run()
    baked.write(args.destination)
