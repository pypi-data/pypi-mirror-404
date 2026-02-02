from __future__ import annotations
from pyclipr.pyclipr import ClipType
from pyclipr.pyclipr import Clipper
from pyclipr.pyclipr import ClipperOffset
from pyclipr.pyclipr import EndType
from pyclipr.pyclipr import FillRule
from pyclipr.pyclipr import JoinType
from pyclipr.pyclipr import PathType
from pyclipr.pyclipr import PolyPath
from pyclipr.pyclipr import PolyTree
from pyclipr.pyclipr import PolyTreeD
from pyclipr.pyclipr import orientation
from pyclipr.pyclipr import polyTreeToPaths
from pyclipr.pyclipr import polyTreeToPaths64
from pyclipr.pyclipr import simplifyPath
from pyclipr.pyclipr import simplifyPaths
from . import pyclipr
__all__: list[str] = ['Clip', 'ClipType', 'Clipper', 'ClipperOffset', 'Difference', 'EndType', 'FillRule', 'Intersection', 'JoinType', 'PathType', 'PolyPath', 'PolyTree', 'PolyTreeD', 'Subject', 'Union', 'Xor', 'clipperVersion', 'orientation', 'polyTreeToPaths', 'polyTreeToPaths64', 'pyclipr', 'simplifyPath', 'simplifyPaths']
Clip: PathType  # value = <PathType.Clip: 1>
Difference: ClipType  # value = <ClipType.Difference: 3>
Intersection: ClipType  # value = <ClipType.Intersection: 1>
Subject: PathType  # value = <PathType.Subject: 0>
Union: ClipType  # value = <ClipType.Union: 2>
Xor: ClipType  # value = <ClipType.Xor: 4>
clipperVersion: str = '2.0.1'
