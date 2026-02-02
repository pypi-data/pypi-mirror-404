"""

        PyClipr Module
        -----------------------
        .. currentmodule:: pyclipr
        .. autosummary::
           :toctree: _generate

    
"""
from __future__ import annotations
import collections.abc
import numpy
import numpy.typing
import typing
__all__: list[str] = ['Clip', 'ClipType', 'Clipper', 'ClipperOffset', 'Difference', 'EndType', 'FillRule', 'Intersection', 'JoinType', 'PathType', 'PolyPath', 'PolyTree', 'PolyTreeD', 'Subject', 'Union', 'Xor', 'clipperVersion', 'orientation', 'polyTreeToPaths', 'polyTreeToPaths64', 'simplifyPath', 'simplifyPaths']
class ClipType:
    """
    The clipping operation type
    
    Members:
    
      Union : Union operation
    
      Difference : Difference operation
    
      Intersection : Intersection operation
    
      Xor : XOR operation
    """
    Difference: typing.ClassVar[ClipType]  # value = <ClipType.Difference: 3>
    Intersection: typing.ClassVar[ClipType]  # value = <ClipType.Intersection: 1>
    Union: typing.ClassVar[ClipType]  # value = <ClipType.Union: 2>
    Xor: typing.ClassVar[ClipType]  # value = <ClipType.Xor: 4>
    __members__: typing.ClassVar[dict[str, ClipType]]  # value = {'Union': <ClipType.Union: 2>, 'Difference': <ClipType.Difference: 3>, 'Intersection': <ClipType.Intersection: 1>, 'Xor': <ClipType.Xor: 4>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __ge__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __gt__(self, other: typing.Any) -> bool:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __le__(self, other: typing.Any) -> bool:
        ...
    def __lt__(self, other: typing.Any) -> bool:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Clipper:
    """
    
        The Clipper class manages the process of clipping polygons using a number of different Boolean operations,
        by providing a list of open or closed subject and clipping paths. These are internally represented with Int64
        precision, that requires the user to specify a scaleFactor. 
    """
    def __init__(self) -> None:
        ...
    def addPath(self, path: typing.Annotated[numpy.typing.ArrayLike, numpy.float64], pathType: PathType, isOpen: bool = False) -> None:
        """
                    The addPath method adds one or more closed subject paths (polygons) to the Clipper object.
        
                    :param path: A list of 2D points (x,y) that define the path. Tuple or a numpy array may be provided
                    :param pathType: A PathType enum value that indicates whether the path is a subject or a clip path.
                    :param isOpen: A boolean value that indicates whether the path is closed or not. Default is 'False'
                    :return: None
        """
    def addPaths(self, paths: collections.abc.Sequence[typing.Annotated[numpy.typing.ArrayLike, numpy.float64]], pathType: PathType, isOpen: bool = False) -> None:
        """
                    The AddPath method adds one or more closed subject paths (polygons) to the Clipper object.
        
                    :param path: A list paths, each consisting 2D points (x,y) that define the path. A Tuple or a numpy array may be provided
                    :param pathType: A PathType enum value that indicates whether the path is a subject or a clip path.
                    :param isOpen: A boolean value that indicates whether the path is closed or not. Default is `False`
                    :param returnZ: If `True`, returns a separate array of the Z attributes for clipped paths. Default is `False`
                    :return: None
        """
    def cleanUp(self) -> None:
        ...
    def clear(self) -> None:
        """
        The clear method removes all the paths from the Clipper object.
        """
    def execute(self, clipType: ClipType, fillRule: FillRule = ..., *, returnOpenPaths: bool = False, returnZ: bool = False) -> typing.Any:
        """
                    The execute method performs the Boolean clipping operation on the polygons or paths that have been added
                    to the clipper object. This method will return a list of paths from the result. The default fillRule is
                    even-odd typically used for the representation of polygons.
        
                    :param clipType: The ClipType or the clipping operation to be used for the paths
                    :param fillRule: A FillType enum value that indicates the fill representation for the paths
                    :param returnOpenPaths: If `True`, returns a tuple consisting of both open and closed paths
                    :param returnZ: If `True`, returns a separate array of the Z attributes for clipped paths. Default is `False`
                    :return: A resultant paths that have been clipped 
        """
    def execute2(self, clipType: ClipType, fillRule: FillRule = ..., *, returnOpenPaths: bool = False, returnZ: bool = False) -> typing.Any:
        """
                    The execute2 method performs the Boolean clipping operation on the polygons or paths that have been added
                    to the clipper object. TThis method will return a PolyTree of the result structuring the output into the hierarchy of
                    the paths that form the exterior and interior polygon.
        
                    The default fillRule is even-odd typically used for the representation of polygons.
        
                    :param clipType: The ClipType or the clipping operation to be used for the paths
                    :param fillRule: A FillType enum value that indicates the fill representation for the paths
                    :param returnOpenPaths: If `True`, returns a tuple consisting of both open and closed paths. Default is `False`
                    :param returnZ: If `True`, returns a separate array of the Z attributes for clipped paths. Default is `False`
                    :return: A resultant polytree of the clipped paths 
        """
    def executeTree(self, clipType: ClipType, fillRule: FillRule = ..., *, returnOpenPaths: bool = False, returnZ: bool = False) -> typing.Any:
        """
                The `executeTree` method performs the Boolean clipping operation on the polygons or paths that have been added
                to the clipper object. TThis method will return a PolyTree of the result structuring the output into the hierarchy of
                the paths that form the exterior and interior polygon.
        
                The default `FillRule` is even-odd typically used for the representation of polygons.
        
                :param clipType: The ClipType or the clipping operation to be used for the paths
                :param fillRule: A FillType enum value that indicates the fill representation for the paths
                :param returnOpenPaths: If `True`, returns a tuple consisting of both open and closed paths. Default is `False`
                :param returnZ: If `True`, returns a separate array of the Z attributes for clipped paths. Default is `False`
                :return: A resultant paths that have been clipped 
        """
    @property
    def preserveCollinear(self) -> bool:
        """
                     By default, when three or more vertices are collinear in input polygons (subject or clip),
                     the Clipper object removes the 'inner' vertices before clipping. When enabled the PreserveCollinear property
                     prevents this default behavior to allow these inner vertices to appear in the solution.
        """
    @preserveCollinear.setter
    def preserveCollinear(self, arg1: bool) -> None:
        ...
    @property
    def scaleFactor(self) -> float:
        """
                    The scale factor to be for transforming the input and output vectors. The default is 1000. 
        """
    @scaleFactor.setter
    def scaleFactor(self, arg1: typing.SupportsFloat) -> None:
        ...
class ClipperOffset:
    """
    
        The ClipperOffset class manages the process of offsetting  (inflating/deflating)
        both open and closed paths using a number of different join types and end types.
        The library user will rarely need to access this unit directly since it will generally
        be easier to use the InflatePaths function when doing polygon offsetting.
    """
    def __init__(self) -> None:
        ...
    def addPath(self, path: typing.Annotated[numpy.typing.ArrayLike, numpy.float64], joinType: JoinType, endType: EndType = ...) -> None:
        """
                    The addPath method adds one open or closed paths (polygon) to the ClipperOffset object.
        
                    :param path: A list of 2D points (x,y) that define the path. Tuple or a numpy array may be provided for the path
                    :param joinType: The JoinType to use for the offsetting / inflation of paths
                    :param endType: The EndType to use for the offsetting / inflation of paths (default is Polygon)
                    :return: None 
        """
    def addPaths(self, path: collections.abc.Sequence[typing.Annotated[numpy.typing.ArrayLike, numpy.float64]], joinType: JoinType, endType: EndType = ...) -> None:
        """
                    The addPath method adds one or more open / closed paths to the ClipperOffset object.
        
                    :param path: A list of paths consisting of 2D points (x,y) that define the path. Tuple or a numpy array may be provided for each path
                    :param joinType: The JoinType to use for the offsetting / inflation of paths
                    :param endType: The EndType to use for the offsetting / inflation of paths
                    :return: None
        """
    def clear(self) -> None:
        """
        The clear method removes all the paths from the ClipperOffset object.
        """
    def execute(self, delta: typing.SupportsFloat) -> typing.Any:
        """
                    The `execute` method performs the offsetting/inflation operation on the polygons or paths that have been added
                    to the clipper object. This method will return a list of paths from the result.
        
                    :param delta: The offset to apply to the inflation/offsetting of paths and segments
                    :return: The resultant offset paths
        """
    def execute2(self, delta: typing.SupportsFloat) -> PolyTreeD:
        """
                    The `execute` method performs the offsetting/inflation operation on the polygons or paths that have been added
                    to the clipper object. This method will return a PolyTree from the result, that considers the hierarchy of the interior and exterior
                    paths of the polygon.
        
                    :param delta: The offset to apply to the inflation/offsetting
                    :return: A resultant offset paths created in a PolyTree64 Object 
        """
    def executeTree(self, delta: typing.SupportsFloat) -> PolyTreeD:
        """
                    The `executeTree` method performs the offsetting/inflation operation on the polygons or paths that have been added
                    to the clipper object. This method will return a PolyTree from the result, that considers the hierarchy of the interior and exterior
                    paths of the polygon.
        
                    :param delta: The offset to apply to the inflation/offsetting
                    :return: A resultant offset paths created in a PolyTree64 Object 
        """
    @property
    def arcTolerance(self) -> float:
        """
                    Firstly, this field/property is only relevant when JoinType = Round and/or EndType = Round.
        
                    Since flattened paths can never perfectly represent arcs, this field/property specifies a maximum acceptable
                    imprecision ('tolerance') when arcs are approximated in an offsetting operation. Smaller values will increase
                    'smoothness' up to a point though at a cost of performance and in creating more vertices to construct the arc.
        
                    The default ArcTolerance is 0.25 units. This means that the maximum distance the flattened path will deviate
                    from the 'true' arc will be no more than 0.25 units (before rounding). 
        """
    @arcTolerance.setter
    def arcTolerance(self, arg1: typing.SupportsFloat) -> None:
        ...
    @property
    def miterLimit(self) -> float:
        """
                     This property sets the maximum distance in multiples of delta that vertices can be offset from their original
                     positions before squaring is applied. (Squaring truncates a miter by 'cutting it off' at 1 x delta distance
                     from the original vertex.)
        
                     The default value for MiterLimit is 2 (ie twice delta). 
        """
    @miterLimit.setter
    def miterLimit(self, arg1: typing.SupportsFloat) -> None:
        ...
    @property
    def preserveCollinear(self) -> bool:
        """
                     By default, when three or more vertices are collinear in input polygons (subject or clip),
                     the Clipper object removes the 'inner' vertices before clipping. When enabled the `PreserveCollinear` property
                     prevents this default behavior to allow these inner vertices to appear in the solution. 
        """
    @preserveCollinear.setter
    def preserveCollinear(self, arg1: bool) -> None:
        ...
    @property
    def scaleFactor(self) -> float:
        """
        Scale factor for transforming the input and output vectors. The default is 1000.
        """
    @scaleFactor.setter
    def scaleFactor(self, arg1: typing.SupportsFloat) -> None:
        ...
class EndType:
    """
    The end type to be used for the offsetting / inflation of paths
    
    Members:
    
      Square : Square end type
    
      Butt : Butt end type
    
      Joined : Joined end type
    
      Polygon : Polygon end type
    
      Round : Round end type
    """
    Butt: typing.ClassVar[EndType]  # value = <EndType.Butt: 2>
    Joined: typing.ClassVar[EndType]  # value = <EndType.Joined: 1>
    Polygon: typing.ClassVar[EndType]  # value = <EndType.Polygon: 0>
    Round: typing.ClassVar[EndType]  # value = <EndType.Round: 4>
    Square: typing.ClassVar[EndType]  # value = <EndType.Square: 3>
    __members__: typing.ClassVar[dict[str, EndType]]  # value = {'Square': <EndType.Square: 3>, 'Butt': <EndType.Butt: 2>, 'Joined': <EndType.Joined: 1>, 'Polygon': <EndType.Polygon: 0>, 'Round': <EndType.Round: 4>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __ge__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __gt__(self, other: typing.Any) -> bool:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __le__(self, other: typing.Any) -> bool:
        ...
    def __lt__(self, other: typing.Any) -> bool:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class FillRule:
    """
    The fill rule to be used for the clipping operation
    
    Members:
    
      EvenOdd : Even and Odd Fill
    
      NonZero : Non-Zero Fill
    
      Positive : Positive Fill
    
      Negative : Negative Fill
    """
    EvenOdd: typing.ClassVar[FillRule]  # value = <FillRule.EvenOdd: 0>
    Negative: typing.ClassVar[FillRule]  # value = <FillRule.Negative: 3>
    NonZero: typing.ClassVar[FillRule]  # value = <FillRule.NonZero: 1>
    Positive: typing.ClassVar[FillRule]  # value = <FillRule.Positive: 2>
    __members__: typing.ClassVar[dict[str, FillRule]]  # value = {'EvenOdd': <FillRule.EvenOdd: 0>, 'NonZero': <FillRule.NonZero: 1>, 'Positive': <FillRule.Positive: 2>, 'Negative': <FillRule.Negative: 3>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __ge__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __gt__(self, other: typing.Any) -> bool:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __le__(self, other: typing.Any) -> bool:
        ...
    def __lt__(self, other: typing.Any) -> bool:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class JoinType:
    """
    The join type to be used for the offsetting / inflation of paths
    
    Members:
    
      Square : Square join type
    
      Round : Round join type
    
      Miter : Miter join type
    """
    Miter: typing.ClassVar[JoinType]  # value = <JoinType.Miter: 3>
    Round: typing.ClassVar[JoinType]  # value = <JoinType.Round: 2>
    Square: typing.ClassVar[JoinType]  # value = <JoinType.Square: 0>
    __members__: typing.ClassVar[dict[str, JoinType]]  # value = {'Square': <JoinType.Square: 0>, 'Round': <JoinType.Round: 2>, 'Miter': <JoinType.Miter: 3>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __ge__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __gt__(self, other: typing.Any) -> bool:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __le__(self, other: typing.Any) -> bool:
        ...
    def __lt__(self, other: typing.Any) -> bool:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class PathType:
    """
    The path type
    
    Members:
    
      Subject : The subject path
    
      Clip : The clipping path
    """
    Clip: typing.ClassVar[PathType]  # value = <PathType.Clip: 1>
    Subject: typing.ClassVar[PathType]  # value = <PathType.Subject: 0>
    __members__: typing.ClassVar[dict[str, PathType]]  # value = {'Subject': <PathType.Subject: 0>, 'Clip': <PathType.Clip: 1>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class PolyPath:
    @property
    def level(self) -> int:
        ...
    @property
    def parent(self) -> PolyPath:
        ...
class PolyTree:
    def __len__(self) -> int:
        ...
    @property
    def area(self) -> float:
        ...
    @property
    def attributes(self) -> typing.Any:
        ...
    @property
    def children(self) -> list[PolyTree]:
        ...
    @property
    def count(self) -> int:
        ...
    @property
    def isHole(self) -> bool:
        ...
    @property
    def polygon(self) -> typing.Any:
        ...
class PolyTreeD:
    def __len__(self) -> int:
        ...
    @property
    def area(self) -> float:
        ...
    @property
    def attributes(self) -> typing.Any:
        ...
    @property
    def children(self) -> list[PolyTreeD]:
        ...
    @property
    def count(self) -> int:
        ...
    @property
    def isHole(self) -> bool:
        ...
    @property
    def polygon(self) -> typing.Any:
        ...
def orientation(path: typing.Annotated[numpy.typing.ArrayLike, numpy.float64], scaleFactor: typing.SupportsFloat = 1000) -> bool:
    """
            This function returns the orientation of a path. Orientation will return `True` if the polygon's orientation
            is counter-clockwise.
    
            :param path: A 2D numpy array of shape (n, 2) or (n, 3) where n is the number of vertices in the path.
            :param scaleFactor: Optional scale factor for the internal clipping factor. Defaults to 1000.
            :return: `True` if the polygon's orientation is counter-clockwise, `False` otherwise.
    """
def polyTreeToPaths(arg0: PolyTree, arg1: typing.SupportsFloat) -> typing.Any:
    ...
def polyTreeToPaths64(arg0: PolyTree, arg1: typing.SupportsFloat) -> typing.Any:
    ...
def simplifyPath(path: typing.Annotated[numpy.typing.ArrayLike, numpy.float64], epsilon: typing.SupportsFloat, scaleFactor: typing.SupportsFloat = 1000, isOpenPath: bool = False) -> typing.Any:
    """
                This function removes vertices that are less than the specified epsilon distance from an imaginary line
                that passes through its two adjacent vertices. Logically, smaller epsilon values will be less aggressive
                in removing vertices than larger epsilon values.
    
                :param path: A 2D numpy array of shape (n, 2) or (n, 3) where n is the number of vertices in the path.
                :param epsilon: The maximum distance a vertex can be from an imaginary line that passes through its two adjacent vertices.
                :param scaleFactor: The scaleFactor applied to the path during simplification
                :param isOpenPath: If `True`, the path is treated as an open path. If `False`, the path is treated as a closed path.
                :return: Simplified path
    """
def simplifyPaths(paths: collections.abc.Sequence[typing.Annotated[numpy.typing.ArrayLike, numpy.float64]], epsilon: typing.SupportsFloat, scaleFactor: typing.SupportsFloat = 1000, isOpenPath: bool = False) -> typing.Any:
    """
                This function removes vertices that are less than the specified epsilon distance from an imaginary line
                that passes through its two adjacent vertices. Logically, smaller epsilon values will be less aggressive
                in removing vertices than larger epsilon values.
    
                :param paths: A list of 2D points (x,y) that define the path. Tuple or a numpy array may be provided for the path
                :param epsilon: The maximum distance a vertex can be from an imaginary line that passes through its 2 adjacent vertices.
                :param scaleFactor: The scaleFactor applied to the path during simplification
                :param isOpenPath: If `True`, the path is treated as an open path. If `False`, the path is treated as a closed path.
                :return: None
    """
Clip: PathType  # value = <PathType.Clip: 1>
Difference: ClipType  # value = <ClipType.Difference: 3>
Intersection: ClipType  # value = <ClipType.Intersection: 1>
Subject: PathType  # value = <PathType.Subject: 0>
Union: ClipType  # value = <ClipType.Union: 2>
Xor: ClipType  # value = <ClipType.Xor: 4>
__version__: str = 'PROJECT_VERSION'
clipperVersion: str = '2.0.1'
