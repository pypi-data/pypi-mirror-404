import os
# Pydantic urls is usually annoying because they make the output nasty and unclear.
# This is the only way to turn off that behaviour and cannot be undone in runtime.
os.environ['PYDANTIC_ERRORS_INCLUDE_URL'] = '0'



# :: AUTOGEN-START ::

from .aff import AFF, ArcType, ArcColor, Arctap, Arc, ScaledArctap, CameraEasing, Camera, Hold, HoldFloat, SceneControlType, SceneControl, Tap, TapFloat, Timing, analyse_annotation, analyse_part_separation, analyse_timinggroup_header, analyse_timinggroup_footer, analyse_command, TokenType, Token, Tokens, ARG_TOKEN_TYPES, COMMAND_TOKEN_TYPES, TOKEN_TYPES_PATTERNS, tokenize, parse_event, TimingGroup, FixedLane, FloatLane, ArcCoord, Coordinate, dffloat, dffloat2, dffloat3, BaseEasing, EasingLinear, EasingSineIn, EasingSineOut, EasingBezierDefault, EasingSineInOut, ArcEasing, get_easing_x, get_easing_y, HitsoundStr, AFFEventConfig, AFFEvent, GameObjectEvent, TechnicalEvent, FloorEvent, SkyEvent, LongNoteEvent, TapLikeEvent
from .globcfg import GlobalConfig
from .songlist import Difficulty, Difficulties, SonglistItem, LowerAsciiId, BackgroundStr, SingleLineStr, GuardinaError, Localized, LocalizedReqEn, StrLocalizedSLRE, SideEnum, RatingClassEnum, RTCLS_STR_MAP, RatingInt, Backgrounds, BACKGROUNDS
from .utils import classproperty, get_default_model_cfg, UnreachableBranch, Predicate

__all__ = [
    'AFF', 
    'ArcType', 
    'ArcColor', 
    'Arctap', 
    'Arc', 
    'ScaledArctap', 
    'CameraEasing', 
    'Camera', 
    'Hold', 
    'HoldFloat', 
    'SceneControlType', 
    'SceneControl', 
    'Tap', 
    'TapFloat', 
    'Timing', 
    'analyse_annotation', 
    'analyse_part_separation', 
    'analyse_timinggroup_header', 
    'analyse_timinggroup_footer', 
    'analyse_command', 
    'TokenType', 
    'Token', 
    'Tokens', 
    'ARG_TOKEN_TYPES', 
    'COMMAND_TOKEN_TYPES', 
    'TOKEN_TYPES_PATTERNS', 
    'tokenize', 
    'parse_event', 
    'TimingGroup', 
    'FixedLane', 
    'FloatLane', 
    'ArcCoord', 
    'Coordinate', 
    'dffloat', 
    'dffloat2', 
    'dffloat3', 
    'BaseEasing', 
    'EasingLinear', 
    'EasingSineIn', 
    'EasingSineOut', 
    'EasingBezierDefault', 
    'EasingSineInOut', 
    'ArcEasing', 
    'get_easing_x', 
    'get_easing_y', 
    'HitsoundStr', 
    'AFFEventConfig', 
    'AFFEvent', 
    'GameObjectEvent', 
    'TechnicalEvent', 
    'FloorEvent', 
    'SkyEvent', 
    'LongNoteEvent', 
    'TapLikeEvent', 
    'GlobalConfig', 
    'Difficulty', 
    'Difficulties', 
    'SonglistItem', 
    'LowerAsciiId', 
    'BackgroundStr', 
    'SingleLineStr', 
    'GuardinaError', 
    'Localized', 
    'LocalizedReqEn', 
    'StrLocalizedSLRE', 
    'SideEnum', 
    'RatingClassEnum', 
    'RTCLS_STR_MAP', 
    'RatingInt', 
    'Backgrounds', 
    'BACKGROUNDS', 
    'classproperty', 
    'get_default_model_cfg', 
    'UnreachableBranch', 
    'Predicate', 
]

# :: AUTOGEN-END ::
