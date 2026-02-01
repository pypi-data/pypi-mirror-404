__all__ = [
    "HtmlElement",
    "HeadElement",
    "TitleElement",
    "BaseElement",
    "LinkElement",
    "MetaElement",
    "StyleElement",
    "BodyElement",
    "ArticleElement",
    "SectionElement",
    "NavigationElement",
    "AsideElement",
    "HeadingLevel1Element",
    "HeadingLevel2Element",
    "HeadingLevel3Element",
    "HeadingLevel4Element",
    "HeadingLevel5Element",
    "HeadingLevel6Element",
    "HeadingGroupElement",
    "HeaderElement",
    "FooterElement",
    "AddressElement",
    "ParagraphElement",
    "HorizontalRuleElement",
    "PreformattedTextElement",
    "BlockQuotationElement",
    "OrderedListElement",
    "UnorderedListElement",
    "MenuElement",
    "ListItemElement",
    "DescriptionListElement",
    "DescriptionTermElement",
    "DescriptionDetailsElement",
    "FigureElement",
    "FigureCaptionElement",
    "MainElement",
    "SearchElement",
    "DivisionElement",
    "AnchorElement",
    "EmphasisElement",
    "StrongImportanceElement",
    "SmallPrintElement",
    "StrikethroughElement",
    "CitationElement",
    "QuotationElement",
    "DefinitionElement",
    "AbbreviationElement",
    "RubyAnnotationElement",
    "RubyTextElement",
    "RubyParenthesesElement",
    "DataElement",
    "TimeElement",
    "CodeElement",
    "VariableElement",
    "SampleElement",
    "KeyboardInputElement",
    "SubscriptElement",
    "SuperscriptElement",
    "ItalicTextElement",
    "BoldTextElement",
    "UnarticulatedAnnotationElement",
    "MarkedTextElement",
    "BidirectionalIsolateElement",
    "BidirectionalOverrideElement",
    "SpanElement",
    "LineBreakElement",
    "LineBreakOpportunityElement",
    "InsertionElement",
    "DeletionElement",
    "PictureElement",
    "SourceElement",
    "ImageElement",
    "InlineFrameElement",
    "EmbeddedContentElement",
    "ExternalObjectElement",
    "VideoElement",
    "AudioElement",
    "TextTrackElement",
    "ImageMapElement",
    "ImageMapAreaElement",
    "TableElement",
    "TableCaptionElement",
    "TableColumnGroupElement",
    "TableColumnElement",
    "TableBodyElement",
    "TableHeadElement",
    "TableFootElement",
    "TableRowElement",
    "TableDataCellElement",
    "TableHeaderCellElement",
    "FormElement",
    "LabelElement",
    "InputElement",
    "ButtonElement",
    "SelectElement",
    "DataListElement",
    "OptionGroupElement",
    "OptionElement",
    "TextAreaElement",
    "OutputElement",
    "ProgressElement",
    "MeterElement",
    "FieldSetElement",
    "FieldSetLegendElement",
    "DetailsElement",
    "SummaryElement",
    "DialogElement",
    "ScriptElement",
    "NoScriptElement",
    "TemplateElement",
    "SlotElement",
    "CanvasElement",
    "SVGElement",
    "SVGAnchorElement",
    "SVGAnimateElement",
    "SVGAnimateMotionElement",
    "SVGAnimateTransformElement",
    "SVGCircleElement",
    "SVGClipPathElement",
    "SVGDefinitionsElement",
    "SVGDescriptionElement",
    "SVGEllipseElement",
    "SVGFilterElement",
    "SVGFilterBlendElement",
    "SVGFilterColorMatrixElement",
    "SVGFilterComponentTransferElement",
    "SVGFilterCompositeElement",
    "SVGFilterConvolveMatrixElement",
    "SVGFilterDiffuseLightingElement",
    "SVGFilterDisplacementMapElement",
    "SVGFilterDistantLightElement",
    "SVGFilterDropShadowElement",
    "SVGFilterFloodElement",
    "SVGFilterFunctionAlphaElement",
    "SVGFilterFunctionBlueElement",
    "SVGFilterFunctionGreenElement",
    "SVGFilterFunctionRedElement",
    "SVGFilterGaussianBlurElement",
    "SVGFilterImageElement",
    "SVGFilterMergeElement",
    "SVGFilterMergeNodeElement",
    "SVGFilterMorphologyElement",
    "SVGFilterOffsetElement",
    "SVGFilterPointLightElement",
    "SVGFilterSpecularLightingElement",
    "SVGFilterSpotLightElement",
    "SVGFilterTileElement",
    "SVGFilterTurbulenceElement",
    "SVGForeignObjectElement",
    "SVGGroupElement",
    "SVGImageElement",
    "SVGLineElement",
    "SVGLinearGradientElement",
    "SVGMarkerElement",
    "SVGMaskElement",
    "SVGMetadataElement",
    "SVGMotionPathElement",
    "SVGPathElement",
    "SVGPatternElement",
    "SVGPolygonElement",
    "SVGPolylineElement",
    "SVGRadialGradientElement",
    "SVGRectangleElement",
    "SVGScriptElement",
    "SVGSetElement",
    "SVGStopElement",
    "SVGStyleElement",
    "SVGSwitchElement",
    "SVGSymbolElement",
    "SVGTextElement",
    "SVGTextPathElement",
    "SVGTextSpanElement",
    "SVGTitleElement",
    "SVGUseElement",
    "SVGViewElement",
]

from ..core import OpenElement, ClosedElement, TextNode

# --- The document element ---

class HtmlElement(OpenElement):
    tag = "html"
    render_mode = "block"

# --- Document metadata ---

class HeadElement(OpenElement):
    tag = "head"
    render_mode = "block"

class TitleElement(OpenElement):
    tag = "title"
    render_mode = "preformatted"

class BaseElement(ClosedElement):
    tag = "base"
    render_mode = "block"

class LinkElement(ClosedElement):
    tag = "link"
    render_mode = "block"

class MetaElement(ClosedElement):
    tag = "meta"
    render_mode = "block"

class StyleElement(OpenElement):
    tag = "style"
    render_mode = "preformatted"

    def __init__(self, *args, escape_tag_delimiters = None, **kwargs):
        if escape_tag_delimiters is None:
            # stylesheets might contain angle brackets, so it is better to
            # disable tag delimiter escaping by default
            escape_tag_delimiters = False
        super().__init__(
            *args,
            escape_tag_delimiters=escape_tag_delimiters,
            **kwargs
        )

    def expand(self, context: "ophinode.site.BuildContext"):
        expansion = []
        for c in self._children:
            if isinstance(c, str):
                # Stylesheets might contain "</style", so it must be escaped
                content = c.replace("</style", "\\3C/style")
                node = TextNode(content)
                if self._escape_ampersands is not None:
                    node.escape_ampersands(self._escape_ampersands)
                if self._escape_tag_delimiters is not None:
                    node.escape_tag_delimiters(self._escape_tag_delimiters)
                expansion.append(node)
            else:
                expansion.append(c)
        return expansion

# --- Sections ---

class BodyElement(OpenElement):
    tag = "body"
    render_mode = "block"

class ArticleElement(OpenElement):
    tag = "article"
    render_mode = "block"

class SectionElement(OpenElement):
    tag = "section"
    render_mode = "block"

class NavigationElement(OpenElement):
    tag = "nav"
    render_mode = "block"

class AsideElement(OpenElement):
    tag = "aside"
    render_mode = "block"

class HeadingLevel1Element(OpenElement):
    tag = "h1"
    render_mode = "block"

class HeadingLevel2Element(OpenElement):
    tag = "h2"
    render_mode = "block"

class HeadingLevel3Element(OpenElement):
    tag = "h3"
    render_mode = "block"

class HeadingLevel4Element(OpenElement):
    tag = "h4"
    render_mode = "block"

class HeadingLevel5Element(OpenElement):
    tag = "h5"
    render_mode = "block"

class HeadingLevel6Element(OpenElement):
    tag = "h6"
    render_mode = "block"

class HeadingGroupElement(OpenElement):
    tag = "hgroup"
    render_mode = "block"

class HeaderElement(OpenElement):
    tag = "header"
    render_mode = "block"

class FooterElement(OpenElement):
    tag = "footer"
    render_mode = "block"

class AddressElement(OpenElement):
    tag = "address"
    render_mode = "block"

# --- Grouping content ---

class ParagraphElement(OpenElement):
    tag = "p"
    render_mode = "block"

class HorizontalRuleElement(ClosedElement):
    tag = "hr"
    render_mode = "block"

class PreformattedTextElement(OpenElement):
    tag = "pre"
    render_mode = "preformatted"

class BlockQuotationElement(OpenElement):
    tag = "blockquote"
    render_mode = "block"

class OrderedListElement(OpenElement):
    tag = "ol"
    render_mode = "block"

class UnorderedListElement(OpenElement):
    tag = "ul"
    render_mode = "block"

class MenuElement(OpenElement):
    tag = "menu"
    render_mode = "block"

class ListItemElement(OpenElement):
    tag = "li"
    render_mode = "block"

class DescriptionListElement(OpenElement):
    tag = "dl"
    render_mode = "block"

class DescriptionTermElement(OpenElement):
    tag = "dt"
    render_mode = "block"

class DescriptionDetailsElement(OpenElement):
    tag = "dd"
    render_mode = "block"

class FigureElement(OpenElement):
    tag = "figure"
    render_mode = "block"

class FigureCaptionElement(OpenElement):
    tag = "figcaption"
    render_mode = "block"

class MainElement(OpenElement):
    tag = "main"
    render_mode = "block"

class SearchElement(OpenElement):
    tag = "search"
    render_mode = "block"

class DivisionElement(OpenElement):
    tag = "div"
    render_mode = "block"

# --- Text-level semantics ---

class AnchorElement(OpenElement):
    tag = "a"
    render_mode = "inline"

class EmphasisElement(OpenElement):
    tag = "em"
    render_mode = "inline"

class StrongImportanceElement(OpenElement):
    tag = "strong"
    render_mode = "inline"

class SmallPrintElement(OpenElement):
    tag = "small"
    render_mode = "inline"

class StrikethroughElement(OpenElement):
    tag = "s"
    render_mode = "inline"

class CitationElement(OpenElement):
    tag = "cite"
    render_mode = "inline"

class QuotationElement(OpenElement):
    tag = "q"
    render_mode = "inline"

class DefinitionElement(OpenElement):
    tag = "dfn"
    render_mode = "inline"

class AbbreviationElement(OpenElement):
    tag = "abbr"
    render_mode = "inline"

class RubyAnnotationElement(OpenElement):
    tag = "ruby"
    render_mode = "inline"

class RubyTextElement(OpenElement):
    tag = "rt"
    render_mode = "inline"

class RubyParenthesesElement(OpenElement):
    tag = "rp"
    render_mode = "inline"

class DataElement(OpenElement):
    tag = "data"
    render_mode = "inline"

class TimeElement(OpenElement):
    tag = "time"
    render_mode = "inline"

class CodeElement(OpenElement):
    tag = "code"
    render_mode = "inline"

class VariableElement(OpenElement):
    tag = "var"
    render_mode = "inline"

class SampleElement(OpenElement):
    tag = "samp"
    render_mode = "inline"

class KeyboardInputElement(OpenElement):
    tag = "kbd"
    render_mode = "inline"

class SubscriptElement(OpenElement):
    tag = "sub"
    render_mode = "inline"

class SuperscriptElement(OpenElement):
    tag = "sup"
    render_mode = "inline"

class ItalicTextElement(OpenElement):
    tag = "i"
    render_mode = "inline"

class BoldTextElement(OpenElement):
    tag = "b"
    render_mode = "inline"

class UnarticulatedAnnotationElement(OpenElement):
    tag = "u"
    render_mode = "inline"

class MarkedTextElement(OpenElement):
    tag = "mark"
    render_mode = "inline"

class BidirectionalIsolateElement(OpenElement):
    tag = "bdi"
    render_mode = "inline"

class BidirectionalOverrideElement(OpenElement):
    tag = "bdo"
    render_mode = "inline"

class SpanElement(OpenElement):
    tag = "span"
    render_mode = "inline"

class LineBreakElement(ClosedElement):
    tag = "br"
    render_mode = "inline"

class LineBreakOpportunityElement(ClosedElement):
    tag = "wbr"
    render_mode = "inline"

# --- Edits ---

class InsertionElement(OpenElement):
    tag = "ins"
    render_mode = "inline"

class DeletionElement(OpenElement):
    tag = "del"
    render_mode = "inline"

# --- Embedded content ---

class PictureElement(OpenElement):
    tag = "picture"
    render_mode = "inline"

class SourceElement(ClosedElement):
    tag = "source"
    render_mode = "inline"

class ImageElement(ClosedElement):
    tag = "img"
    render_mode = "inline"

class InlineFrameElement(OpenElement):
    tag = "iframe"
    render_mode = "inline"

class EmbeddedContentElement(ClosedElement):
    tag = "embed"
    render_mode = "inline"

class ExternalObjectElement(OpenElement):
    tag = "object"
    render_mode = "inline"

class VideoElement(OpenElement):
    tag = "video"
    render_mode = "inline"

class AudioElement(OpenElement):
    tag = "audio"
    render_mode = "inline"

class TextTrackElement(ClosedElement):
    tag = "track"
    render_mode = "inline"

class ImageMapElement(OpenElement):
    tag = "map"
    render_mode = "inline"

class ImageMapAreaElement(ClosedElement):
    tag = "area"
    render_mode = "inline"

# --- Tabular data ---

class TableElement(OpenElement):
    tag = "table"
    render_mode = "block"

class TableCaptionElement(OpenElement):
    tag = "caption"
    render_mode = "block"

class TableColumnGroupElement(OpenElement):
    tag = "colgroup"
    render_mode = "block"

class TableColumnElement(ClosedElement):
    tag = "col"
    render_mode = "block"

class TableBodyElement(OpenElement):
    tag = "tbody"
    render_mode = "block"

class TableHeadElement(OpenElement):
    tag = "thead"
    render_mode = "block"

class TableFootElement(OpenElement):
    tag = "tfoot"
    render_mode = "block"

class TableRowElement(OpenElement):
    tag = "tr"
    render_mode = "block"

class TableDataCellElement(OpenElement):
    tag = "td"
    render_mode = "block"

class TableHeaderCellElement(OpenElement):
    tag = "th"
    render_mode = "block"

# --- Forms ---

class FormElement(OpenElement):
    tag = "form"
    render_mode = "block"

class LabelElement(OpenElement):
    tag = "label"
    render_mode = "inline"

class InputElement(ClosedElement):
    tag = "input"
    render_mode = "inline"

class ButtonElement(OpenElement):
    tag = "button"
    render_mode = "inline"

class SelectElement(OpenElement):
    tag = "select"
    render_mode = "inline"

class DataListElement(OpenElement):
    tag = "datalist"
    render_mode = "block"

class OptionGroupElement(OpenElement):
    tag = "optgroup"
    render_mode = "block"

class OptionElement(OpenElement):
    tag = "option"
    render_mode = "block"

class TextAreaElement(OpenElement):
    tag = "textarea"
    render_mode = "inline-preformatted"

class OutputElement(OpenElement):
    tag = "output"
    render_mode = "inline"

class ProgressElement(OpenElement):
    tag = "progress"
    render_mode = "inline"

class MeterElement(OpenElement):
    tag = "meter"
    render_mode = "inline"

class FieldSetElement(OpenElement):
    tag = "fieldset"
    render_mode = "block"

class FieldSetLegendElement(OpenElement):
    tag = "legend"
    render_mode = "block"

# --- Interactive elements ---

class DetailsElement(OpenElement):
    tag = "details"
    render_mode = "block"

class SummaryElement(OpenElement):
    tag = "summary"
    render_mode = "block"

class DialogElement(OpenElement):
    tag = "dialog"
    render_mode = "block"

# --- Scripting ---

class ScriptElement(OpenElement):
    tag = "script"
    render_mode = "preformatted"

    def __init__(self, *args, escape_tag_delimiters = None, **kwargs):
        if escape_tag_delimiters is None:
            # javascript code might contain angle brackets,
            # so it is better to disable tag delimiter escaping by default
            escape_tag_delimiters = False
        super().__init__(
            *args,
            escape_tag_delimiters=escape_tag_delimiters,
            **kwargs
        )

    def expand(self, context: "ophinode.site.BuildContext"):
        expansion = []
        for c in self._children:
            if isinstance(c, str):
                # Due to restrictions for contents of script elements, some
                # sequences of characters must be replaced before constructing
                # a script element.
                # 
                # Unfortunately, correctly replacing such character sequences
                # require a full lexical analysis on the script content, but
                # ophinode is currently incapable of doing so.
                #
                # However, the sequences are expected to be rarely seen
                # outside literals, so replacements are done nonetheless.
                #
                # This behavior might change in the later versions of ophinode
                # when it starts to better support inline scripting.
                #
                # Read https://html.spec.whatwg.org/multipage/scripting.html#restrictions-for-contents-of-script-elements
                # for more information.
                #
                content = c.replace(
                    "<!--", "\\x3C!--"
                ).replace(
                    "<script", "\\x3Cscript"
                ).replace(
                    "</script", "\\x3C/script"
                )
                node = TextNode(content)
                if self._escape_ampersands is not None:
                    node.escape_ampersands(self._escape_ampersands)
                if self._escape_tag_delimiters is not None:
                    node.escape_tag_delimiters(self._escape_tag_delimiters)
                expansion.append(node)
            else:
                expansion.append(c)
        return expansion

class NoScriptElement(OpenElement):
    tag = "noscript"
    render_mode = "inline"

class TemplateElement(OpenElement):
    tag = "template"
    render_mode = "preformatted"

class SlotElement(OpenElement):
    tag = "slot"
    render_mode = "preformatted"

class CanvasElement(OpenElement):
    tag = "canvas"
    render_mode = "inline"

# --- SVG elements ---

class SVGElement(OpenElement):
    tag = "svg"
    render_mode = "block"

class SVGAnchorElement(OpenElement):
    tag = "a"
    render_mode = "block"

class SVGAnimateElement(OpenElement):
    tag = "animate"
    render_mode = "block"

class SVGAnimateMotionElement(OpenElement):
    tag = "animateMotion"
    render_mode = "block"

class SVGAnimateTransformElement(OpenElement):
    tag = "animateTransform"
    render_mode = "block"

class SVGCircleElement(OpenElement):
    tag = "circle"
    render_mode = "block"

class SVGClipPathElement(OpenElement):
    tag = "clipPath"
    render_mode = "block"

class SVGDefinitionsElement(OpenElement):
    tag = "defs"
    render_mode = "block"

class SVGDescriptionElement(OpenElement):
    tag = "desc"
    render_mode = "block"

class SVGEllipseElement(OpenElement):
    tag = "ellipse"
    render_mode = "block"

class SVGFilterElement(OpenElement):
    tag = "filter"
    render_mode = "block"

class SVGFilterBlendElement(OpenElement):
    tag = "feBlend"
    render_mode = "block"

class SVGFilterColorMatrixElement(OpenElement):
    tag = "feColorMatrix"
    render_mode = "block"

class SVGFilterComponentTransferElement(OpenElement):
    tag = "feComponentTransfer"
    render_mode = "block"

class SVGFilterCompositeElement(OpenElement):
    tag = "feComposite"
    render_mode = "block"

class SVGFilterConvolveMatrixElement(OpenElement):
    tag = "feConvolveMatrix"
    render_mode = "block"

class SVGFilterDiffuseLightingElement(OpenElement):
    tag = "feDiffuseLighting"
    render_mode = "block"

class SVGFilterDisplacementMapElement(OpenElement):
    tag = "feDisplacementMap"
    render_mode = "block"

class SVGFilterDistantLightElement(OpenElement):
    tag = "feDistantLight"
    render_mode = "block"

class SVGFilterDropShadowElement(OpenElement):
    tag = "feDropShadow"
    render_mode = "block"

class SVGFilterFloodElement(OpenElement):
    tag = "feFlood"
    render_mode = "block"

class SVGFilterFunctionAlphaElement(OpenElement):
    tag = "feFuncA"
    render_mode = "block"

class SVGFilterFunctionBlueElement(OpenElement):
    tag = "feFuncB"
    render_mode = "block"

class SVGFilterFunctionGreenElement(OpenElement):
    tag = "feFuncG"
    render_mode = "block"

class SVGFilterFunctionRedElement(OpenElement):
    tag = "feFuncR"
    render_mode = "block"

class SVGFilterGaussianBlurElement(OpenElement):
    tag = "feGaussianBlur"
    render_mode = "block"

class SVGFilterImageElement(OpenElement):
    tag = "feImage"
    render_mode = "block"

class SVGFilterMergeElement(OpenElement):
    tag = "feMerge"
    render_mode = "block"

class SVGFilterMergeNodeElement(OpenElement):
    tag = "feMergeNode"
    render_mode = "block"

class SVGFilterMorphologyElement(OpenElement):
    tag = "feMorphology"
    render_mode = "block"

class SVGFilterOffsetElement(OpenElement):
    tag = "feOffset"
    render_mode = "block"

class SVGFilterPointLightElement(OpenElement):
    tag = "fePointLight"
    render_mode = "block"

class SVGFilterSpecularLightingElement(OpenElement):
    tag = "feSpecularLighting"
    render_mode = "block"

class SVGFilterSpotLightElement(OpenElement):
    tag = "feSpotLight"
    render_mode = "block"

class SVGFilterTileElement(OpenElement):
    tag = "feTile"
    render_mode = "block"

class SVGFilterTurbulenceElement(OpenElement):
    tag = "feTurbulence"
    render_mode = "block"

class SVGForeignObjectElement(OpenElement):
    tag = "foreignObject"
    render_mode = "block"

class SVGGroupElement(OpenElement):
    tag = "g"
    render_mode = "block"

class SVGImageElement(OpenElement):
    tag = "image"
    render_mode = "block"

class SVGLineElement(OpenElement):
    tag = "line"
    render_mode = "block"

class SVGLinearGradientElement(OpenElement):
    tag = "linearGradient"
    render_mode = "block"

class SVGMarkerElement(OpenElement):
    tag = "marker"
    render_mode = "block"

class SVGMaskElement(OpenElement):
    tag = "mask"
    render_mode = "block"

class SVGMetadataElement(OpenElement):
    tag = "metadata"
    render_mode = "block"

class SVGMotionPathElement(OpenElement):
    tag = "mpath"
    render_mode = "block"

class SVGPathElement(OpenElement):
    tag = "path"
    render_mode = "block"

class SVGPatternElement(OpenElement):
    tag = "pattern"
    render_mode = "block"

class SVGPolygonElement(OpenElement):
    tag = "polygon"
    render_mode = "block"

class SVGPolylineElement(OpenElement):
    tag = "polyline"
    render_mode = "block"

class SVGRadialGradientElement(OpenElement):
    tag = "radialGradient"
    render_mode = "block"

class SVGRectangleElement(OpenElement):
    tag = "rect"
    render_mode = "block"

class SVGScriptElement(OpenElement):
    tag = "script"
    render_mode = "block"

class SVGSetElement(OpenElement):
    tag = "set"
    render_mode = "block"

class SVGStopElement(OpenElement):
    tag = "stop"
    render_mode = "block"

class SVGStyleElement(OpenElement):
    tag = "style"
    render_mode = "block"

class SVGSwitchElement(OpenElement):
    tag = "switch"
    render_mode = "block"

class SVGSymbolElement(OpenElement):
    tag = "symbol"
    render_mode = "block"

class SVGTextElement(OpenElement):
    tag = "text"
    render_mode = "block"

class SVGTextPathElement(OpenElement):
    tag = "textPath"
    render_mode = "block"

class SVGTextSpanElement(OpenElement):
    tag = "tspan"
    render_mode = "block"

class SVGTitleElement(OpenElement):
    tag = "title"
    render_mode = "block"

class SVGUseElement(OpenElement):
    tag = "use"
    render_mode = "block"

class SVGViewElement(OpenElement):
    tag = "view"
    render_mode = "block"
