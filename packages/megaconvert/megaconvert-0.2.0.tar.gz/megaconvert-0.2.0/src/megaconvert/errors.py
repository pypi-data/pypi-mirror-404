class MegaConvertError(Exception):
    pass

class NoConverterFound(MegaConvertError):
    pass

class ToolMissing(MegaConvertError):
    pass

class ConversionFailed(MegaConvertError):
    pass

class InvalidRequest(MegaConvertError):
    pass
