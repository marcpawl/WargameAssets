import xml.dom.minidom
from xml.dom.minidom import Attr, Element, Node
import sys
from pathlib import Path
from enum import Enum
from typing import Dict


XMLNS_INKSCAPE = "http://www.inkscape.org/namespaces/inkscape"

# 0.001 inches in mm
CUTTING_STROKE_WIDTH = "0.0360226"

class State(Enum):
    DEFAULT = 0
    IN_CUT = 1
    IN_ENGRAVE = 2


def splitStyle(style: str) -> Dict[str,str]:
    stylePartsStrings = style.split(";")
    styleParts = dict()
    for stylePart in stylePartsStrings:
        (name,value) = stylePart.split(":")
        styleParts[name] = value
    return styleParts


def cutStyle(node: Node, state: State):
    """Change the style for cutting"""
    if state != State.IN_CUT:
        return
    if node.nodeType != Node.ELEMENT_NODE:
        return
    element: Element = node
    if element.hasAttribute("style") :
        attribute: str = element.getAttribute("style")
        styleParts = splitStyle(attribute)
        if 'opacity' in styleParts:
            styleParts['opacity'] = "1"
        if 'fill' in styleParts:
            styleParts['fill'] = "none"
        if 'stroke-width' in styleParts:
            styleParts['stroke-width'] = CUTTING_STROKE_WIDTH
        newStringParts = map(lambda part: part + ":" + styleParts[part], styleParts)
        newValue = ";".join(newStringParts)
        element.setAttribute("style", newValue)


def engraveStyle(node: Node, state: State):
    """Change the style for engraving"""
    if state != State.IN_ENGRAVE:
        return
    # no changes


def getNewState(element: Element, state: State) -> State:
    if element.hasAttributeNS(XMLNS_INKSCAPE, "label") :
        attribute: str = element.getAttributeNS(XMLNS_INKSCAPE, "label")
        if attribute == "cut":
            return State.IN_CUT
        if attribute == "engrave":
            return State.IN_ENGRAVE
    return state


def cutElements(node: Node, state: State):
    """Transform for cutting"""
    if node.nodeType != Node.ELEMENT_NODE:
        for child in node.childNodes:
            cutElements(child, state)
        return

    element: Element = node
    newState: State = getNewState(element, state)
    if newState == State.IN_ENGRAVE:
        node.unlink()
        return
    
    cutStyle(element, newState)
    for child in node.childNodes:
        cutElements(child, newState)
         

def engraveElements(node: Node, state: State):
    """Transform for engraving"""
    if node.nodeType != Node.ELEMENT_NODE:
        for child in node.childNodes:
            engraveElements(child, state)
        return

    element: Element = node
    newState: State = getNewState(element, state)
    if newState == State.IN_CUT:
        node.unlink()
        return
    
    engraveStyle(element, newState)
    for child in node.childNodes:
        engraveElements(child, newState)


def cut(inputPath: Path, outputPath: Path ):
    with open(inputPath.name, "r") as input:
        doc = xml.dom.minidom.parse(file=input)
        cutElements(doc, State.DEFAULT)
    with open(outputPath, "w") as output:
        doc.writexml(output)


def engrave(inputPath: Path, outputPath: Path ):
    with open(inputPath.name, "r") as input:
        doc = xml.dom.minidom.parse(file=input)
        engraveElements(doc, State.DEFAULT)
    with open(outputPath, "w") as output:
        doc.writexml(output)


inputPath = Path("triumph_all_combined.svg")
cutPath = Path("triumph_all_combined.cut.svg")
engravePath = Path("triumph_all_combined.engrave.svg")
if not inputPath.exists():
    raise Exception("Path does not exist: " + inputPath.name)
cut(inputPath, cutPath)
engrave(inputPath, engravePath)
