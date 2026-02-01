"""
Tikdjoub - Comprehensive Python library for TikTok API signatures generation
"""

from .tikdjoub import (
    # Main functions
    sign,
    UserAgentTik,
    trace_id,
    md5stub,
    xor,
    Newparams,
    xtoken,
    host,
    
    # Classes
    Gorgon,
    Ladon,
    Argus,
    ProtoBuf,
    ProtoReader,
    ProtoWriter,
    ProtoField,
    ProtoError,
    ProtoFieldType,
    SM3,
    ByteBuf,
    
    # Constants
    random_hex,
    get_type_data,
    set_type_data,
    validate,
    __ROR__,
    encrypt_ladon_input,
    encrypt_ladon,
    ladon_encrypt,
    get_bit,
    rotate_left,
    rotate_right,
    key_expansion,
    simon_dec,
    simon_enc,
)

__version__ = "1.0.0"
__author__ = "Tikdjoub Contributors"
__all__ = [
    "sign",
    "UserAgentTik",
    "Gorgon",
    "Ladon",
    "Argus",
    "ProtoBuf",
    "ProtoReader",
    "ProtoWriter",
    "ProtoField",
    "ProtoError",
    "ProtoFieldType",
    "trace_id",
    "md5stub",
    "xor",
    "Newparams",
    "xtoken",
    "host",
    "SM3",
    "ByteBuf",
    "random_hex",
    "get_type_data",
    "set_type_data",
    "validate",
    "__ROR__",
    "encrypt_ladon_input",
    "encrypt_ladon",
    "ladon_encrypt",
    "get_bit",
    "rotate_left",
    "rotate_right",
    "key_expansion",
    "simon_dec",
    "simon_enc",
]
