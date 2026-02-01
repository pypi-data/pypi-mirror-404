__all__ = [
    "Html",
    "Head",
    "Title",
    "Base",
    "Link",
    "Meta",
    "Style",
    "Body",
    "Article",
    "Section",
    "Nav",
    "Aside",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "HGroup",
    "Hgroup",
    "Header",
    "Footer",
    "Address",
    "P",
    "HR",
    "Hr",
    "Pre",
    "BlockQuote",
    "Blockquote",
    "OL",
    "Ol",
    "UL",
    "Ul",
    "Menu",
    "LI",
    "Li",
    "DL",
    "Dl",
    "DT",
    "Dt",
    "DD",
    "Dd",
    "Figure",
    "FigCaption",
    "Figcaption",
    "Main",
    "Search",
    "Div",
    "A",
    "EM",
    "Em",
    "Strong",
    "Small",
    "S",
    "Cite",
    "Q",
    "Dfn",
    "Abbr",
    "Ruby",
    "RT",
    "Rt",
    "RP",
    "Rp",
    "Data",
    "Time",
    "Code",
    "Var",
    "Samp",
    "Kbd",
    "Sub",
    "Sup",
    "I",
    "B",
    "U",
    "Mark",
    "BDI",
    "Bdi",
    "BDO",
    "Bdo",
    "Span",
    "BR",
    "Br",
    "WBR",
    "Wbr",
    "Ins",
    "Del",
    "Picture",
    "Source",
    "Img",
    "IFrame",
    "Iframe",
    "Embed",
    "Object",
    "Video",
    "Audio",
    "Track",
    "Map",
    "Area",
    "Table",
    "Caption",
    "ColGroup",
    "Colgroup",
    "Column",
    "TBody",
    "Tbody",
    "THead",
    "Thead",
    "TFoot",
    "Tfoot",
    "TR",
    "Tr",
    "TD",
    "Td",
    "TH",
    "Th",
    "Form",
    "Label",
    "Input",
    "Button",
    "Select",
    "DataList",
    "Datalist",
    "OptGroup",
    "Optgroup",
    "Option",
    "TextArea",
    "Textarea",
    "Output",
    "Progress",
    "Meter",
    "FieldSet",
    "Fieldset",
    "Legend",
    "Details",
    "Summary",
    "Dialog",
    "Script",
    "NoScript",
    "Noscript",
    "Template",
    "Slot",
    "Canvas",
    "Svg",
    "SvgA",
    "SVGA",
    "Animate",
    "AnimateMotion",
    "AnimateTransform",
    "Circle",
    "ClipPath",
    "Defs",
    "Desc",
    "Ellipse",
    "Filter",
    "FeBlend",
    "FeColorMatrix",
    "FeComponentTransfer",
    "FeComposite",
    "FeConvolveMatrix",
    "FeDiffuseLighting",
    "FeDisplacementMap",
    "FeDistantLight",
    "FeDropShadow",
    "FeFlood",
    "FeFuncA",
    "FeFuncB",
    "FeFuncG",
    "FeFuncR",
    "FeGaussianBlur",
    "FeImage",
    "FeMerge",
    "FeMergeNode",
    "FeMorphology",
    "FeOffset",
    "FePointLight",
    "FeSpecularLighting",
    "FeSpotLight",
    "FeTile",
    "FeTurbulence",
    "ForeignObject",
    "G",
    "Image",
    "Line",
    "LinearGradient",
    "Marker",
    "Mask",
    "Metadata",
    "Mpath",
    "MPath",
    "Path",
    "Pattern",
    "Polygon",
    "Polyline",
    "RadialGradient",
    "Rect",
    "SvgScript",
    "SVGScript",
    "Set",
    "Stop",
    "SvgStyle",
    "SVGStyle",
    "Switch",
    "Symbol",
    "Text",
    "TextPath",
    "Tspan",
    "TSpan",
    "SvgTitle",
    "SVGTitle",
    "Use",
    "View",
]

from .fullname import (
    HtmlElement,
    HeadElement,
    TitleElement,
    BaseElement,
    LinkElement,
    MetaElement,
    StyleElement,
    BodyElement,
    ArticleElement,
    SectionElement,
    NavigationElement,
    AsideElement,
    HeadingLevel1Element,
    HeadingLevel2Element,
    HeadingLevel3Element,
    HeadingLevel4Element,
    HeadingLevel5Element,
    HeadingLevel6Element,
    HeadingGroupElement,
    HeaderElement,
    FooterElement,
    AddressElement,
    ParagraphElement,
    HorizontalRuleElement,
    PreformattedTextElement,
    BlockQuotationElement,
    OrderedListElement,
    UnorderedListElement,
    MenuElement,
    ListItemElement,
    DescriptionListElement,
    DescriptionTermElement,
    DescriptionDetailsElement,
    FigureElement,
    FigureCaptionElement,
    MainElement,
    SearchElement,
    DivisionElement,
    AnchorElement,
    EmphasisElement,
    StrongImportanceElement,
    SmallPrintElement,
    StrikethroughElement,
    CitationElement,
    QuotationElement,
    DefinitionElement,
    AbbreviationElement,
    RubyAnnotationElement,
    RubyTextElement,
    RubyParenthesesElement,
    DataElement,
    TimeElement,
    CodeElement,
    VariableElement,
    SampleElement,
    KeyboardInputElement,
    SubscriptElement,
    SuperscriptElement,
    ItalicTextElement,
    BoldTextElement,
    UnarticulatedAnnotationElement,
    MarkedTextElement,
    BidirectionalIsolateElement,
    BidirectionalOverrideElement,
    SpanElement,
    LineBreakElement,
    LineBreakOpportunityElement,
    InsertionElement,
    DeletionElement,
    PictureElement,
    SourceElement,
    ImageElement,
    InlineFrameElement,
    EmbeddedContentElement,
    ExternalObjectElement,
    VideoElement,
    AudioElement,
    TextTrackElement,
    ImageMapElement,
    ImageMapAreaElement,
    TableElement,
    TableCaptionElement,
    TableColumnGroupElement,
    TableColumnElement,
    TableBodyElement,
    TableHeadElement,
    TableFootElement,
    TableRowElement,
    TableDataCellElement,
    TableHeaderCellElement,
    FormElement,
    LabelElement,
    InputElement,
    ButtonElement,
    SelectElement,
    DataListElement,
    OptionGroupElement,
    OptionElement,
    TextAreaElement,
    OutputElement,
    ProgressElement,
    MeterElement,
    FieldSetElement,
    FieldSetLegendElement,
    DetailsElement,
    SummaryElement,
    DialogElement,
    ScriptElement,
    NoScriptElement,
    TemplateElement,
    SlotElement,
    CanvasElement,
    SVGElement,
    SVGAnchorElement,
    SVGAnimateElement,
    SVGAnimateMotionElement,
    SVGAnimateTransformElement,
    SVGCircleElement,
    SVGClipPathElement,
    SVGDefinitionsElement,
    SVGDescriptionElement,
    SVGEllipseElement,
    SVGFilterElement,
    SVGFilterBlendElement,
    SVGFilterColorMatrixElement,
    SVGFilterComponentTransferElement,
    SVGFilterCompositeElement,
    SVGFilterConvolveMatrixElement,
    SVGFilterDiffuseLightingElement,
    SVGFilterDisplacementMapElement,
    SVGFilterDistantLightElement,
    SVGFilterDropShadowElement,
    SVGFilterFloodElement,
    SVGFilterFunctionAlphaElement,
    SVGFilterFunctionBlueElement,
    SVGFilterFunctionGreenElement,
    SVGFilterFunctionRedElement,
    SVGFilterGaussianBlurElement,
    SVGFilterImageElement,
    SVGFilterMergeElement,
    SVGFilterMergeNodeElement,
    SVGFilterMorphologyElement,
    SVGFilterOffsetElement,
    SVGFilterPointLightElement,
    SVGFilterSpecularLightingElement,
    SVGFilterSpotLightElement,
    SVGFilterTileElement,
    SVGFilterTurbulenceElement,
    SVGForeignObjectElement,
    SVGGroupElement,
    SVGImageElement,
    SVGLineElement,
    SVGLinearGradientElement,
    SVGMarkerElement,
    SVGMaskElement,
    SVGMetadataElement,
    SVGMotionPathElement,
    SVGPathElement,
    SVGPatternElement,
    SVGPolygonElement,
    SVGPolylineElement,
    SVGRadialGradientElement,
    SVGRectangleElement,
    SVGScriptElement,
    SVGSetElement,
    SVGStopElement,
    SVGStyleElement,
    SVGSwitchElement,
    SVGSymbolElement,
    SVGTextElement,
    SVGTextPathElement,
    SVGTextSpanElement,
    SVGTitleElement,
    SVGUseElement,
    SVGViewElement,
)

Html = HtmlElement
Head = HeadElement
Title = TitleElement
Base = BaseElement
Link = LinkElement
Meta = MetaElement
Style = StyleElement
Body = BodyElement
Article = ArticleElement
Section = SectionElement
Nav = NavigationElement
Aside = AsideElement
H1 = HeadingLevel1Element
H2 = HeadingLevel2Element
H3 = HeadingLevel3Element
H4 = HeadingLevel4Element
H5 = HeadingLevel5Element
H6 = HeadingLevel6Element
HGroup = HeadingGroupElement
Hgroup = HeadingGroupElement
Header = HeaderElement
Footer = FooterElement
Address = AddressElement
P = ParagraphElement
HR = HorizontalRuleElement
Hr = HorizontalRuleElement
Pre = PreformattedTextElement
BlockQuote = BlockQuotationElement
Blockquote = BlockQuotationElement
OL = OrderedListElement
Ol = OrderedListElement
UL = UnorderedListElement
Ul = UnorderedListElement
Menu = MenuElement
LI = ListItemElement
Li = ListItemElement
DL = DescriptionListElement
Dl = DescriptionListElement
DT = DescriptionTermElement
Dt = DescriptionTermElement
DD = DescriptionDetailsElement
Dd = DescriptionDetailsElement
Figure = FigureElement
FigCaption = FigureCaptionElement
Figcaption = FigureCaptionElement
Main = MainElement
Search = SearchElement
Div = DivisionElement
A = AnchorElement
EM = EmphasisElement
Em = EmphasisElement
Strong = StrongImportanceElement
Small = SmallPrintElement
S = StrikethroughElement
Cite = CitationElement
Q = QuotationElement
Dfn = DefinitionElement
Abbr = AbbreviationElement
Ruby = RubyAnnotationElement
RT = RubyTextElement
Rt = RubyTextElement
RP = RubyParenthesesElement
Rp = RubyParenthesesElement
Data = DataElement
Time = TimeElement
Code = CodeElement
Var = VariableElement
Samp = SampleElement
Kbd = KeyboardInputElement
Sub = SubscriptElement
Sup = SuperscriptElement
I = ItalicTextElement
B = BoldTextElement
U = UnarticulatedAnnotationElement
Mark = MarkedTextElement
BDI = BidirectionalIsolateElement
Bdi = BidirectionalIsolateElement
BDO = BidirectionalOverrideElement
Bdo = BidirectionalOverrideElement
Span = SpanElement
BR = LineBreakElement
Br = LineBreakElement
WBR = LineBreakOpportunityElement
Wbr = LineBreakOpportunityElement
Ins = InsertionElement
Del = DeletionElement
Picture = PictureElement
Source = SourceElement
Img = ImageElement
IFrame = InlineFrameElement
Iframe = InlineFrameElement
Embed = EmbeddedContentElement
Object = ExternalObjectElement
Video = VideoElement
Audio = AudioElement
Track = TextTrackElement
Map = ImageMapElement
Area = ImageMapAreaElement
Table = TableElement
Caption = TableCaptionElement
ColGroup = TableColumnGroupElement
Colgroup = TableColumnGroupElement
Column = TableColumnElement
TBody = TableBodyElement
Tbody = TableBodyElement
THead = TableHeadElement
Thead = TableHeadElement
TFoot = TableFootElement
Tfoot = TableFootElement
TR = TableRowElement
Tr = TableRowElement
TD = TableDataCellElement
Td = TableDataCellElement
TH = TableHeaderCellElement
Th = TableHeaderCellElement
Form = FormElement
Label = LabelElement
Input = InputElement
Button = ButtonElement
Select = SelectElement
DataList = DataListElement
Datalist = DataListElement
OptGroup = OptionGroupElement
Optgroup = OptionGroupElement
Option = OptionElement
TextArea = TextAreaElement
Textarea = TextAreaElement
Output = OutputElement
Progress = ProgressElement
Meter = MeterElement
FieldSet = FieldSetElement
Fieldset = FieldSetElement
Legend = FieldSetLegendElement
Details = DetailsElement
Summary = SummaryElement
Dialog = DialogElement
Script = ScriptElement
NoScript = NoScriptElement
Noscript = NoScriptElement
Template = TemplateElement
Slot = SlotElement
Canvas = CanvasElement
Svg = SVGElement
SvgA = SVGAnchorElement
SVGA = SVGAnchorElement
Animate = SVGAnimateElement
AnimateMotion = SVGAnimateMotionElement
AnimateTransform = SVGAnimateTransformElement
Circle = SVGCircleElement
ClipPath = SVGClipPathElement
Defs = SVGDefinitionsElement
Desc = SVGDescriptionElement
Ellipse = SVGEllipseElement
Filter = SVGFilterElement
FeBlend = SVGFilterBlendElement
FeColorMatrix = SVGFilterColorMatrixElement
FeComponentTransfer = SVGFilterComponentTransferElement
FeComposite = SVGFilterCompositeElement
FeConvolveMatrix = SVGFilterConvolveMatrixElement
FeDiffuseLighting = SVGFilterDiffuseLightingElement
FeDisplacementMap = SVGFilterDisplacementMapElement
FeDistantLight = SVGFilterDistantLightElement
FeDropShadow = SVGFilterDropShadowElement
FeFlood = SVGFilterFloodElement
FeFuncA = SVGFilterFunctionAlphaElement
FeFuncB = SVGFilterFunctionBlueElement
FeFuncG = SVGFilterFunctionGreenElement
FeFuncR = SVGFilterFunctionRedElement
FeGaussianBlur = SVGFilterGaussianBlurElement
FeImage = SVGFilterImageElement
FeMerge = SVGFilterMergeElement
FeMergeNode = SVGFilterMergeNodeElement
FeMorphology = SVGFilterMorphologyElement
FeOffset = SVGFilterOffsetElement
FePointLight = SVGFilterPointLightElement
FeSpecularLighting = SVGFilterSpecularLightingElement
FeSpotLight = SVGFilterSpotLightElement
FeTile = SVGFilterTileElement
FeTurbulence = SVGFilterTurbulenceElement
ForeignObject = SVGForeignObjectElement
G = SVGGroupElement
Image = SVGImageElement
Line = SVGLineElement
LinearGradient = SVGLinearGradientElement
Marker = SVGMarkerElement
Mask = SVGMaskElement
Metadata = SVGMetadataElement
Mpath = SVGMotionPathElement
MPath = SVGMotionPathElement
Path = SVGPathElement
Pattern = SVGPatternElement
Polygon = SVGPolygonElement
Polyline = SVGPolylineElement
RadialGradient = SVGRadialGradientElement
Rect = SVGRectangleElement
SvgScript = SVGScriptElement
SVGScript = SVGScriptElement
Set = SVGSetElement
Stop = SVGStopElement
SvgStyle = SVGStyleElement
SVGStyle = SVGStyleElement
Switch = SVGSwitchElement
Symbol = SVGSymbolElement
Text = SVGTextElement
TextPath = SVGTextPathElement
Tspan = SVGTextSpanElement
TSpan = SVGTextSpanElement
SvgTitle = SVGTitleElement
SVGTitle = SVGTitleElement
Use = SVGUseElement
View = SVGViewElement

