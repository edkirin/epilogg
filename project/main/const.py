
# ################################################################################
# log entry formats

FormatPlain = 0
FormatJson = 1
FormatXML = 2
FormatYAML = 3

FormatChoices = (
    (FormatPlain, "Plain"),
    (FormatJson, "Json"),
    (FormatXML, "XML"),
    (FormatYAML, "YAML"),
)


# ################################################################################
# log entry levels

LevelNotSet = 0
LevelDebug = 10
LevelInfo = 20
LevelWarning = 30
LevelError = 40
LevelCritical = 50
LevelChoices = (
    (LevelNotSet, "Not set"),
    (LevelDebug, "Debug"),
    (LevelInfo, "Info"),
    (LevelWarning, "Warning"),
    (LevelError, "Error"),
    (LevelCritical, "Critical"),
)

LevelLabelClass = {
    LevelNotSet: 'label-default',
    LevelDebug: 'label-info',
    LevelInfo: 'label-primary',
    LevelWarning: 'label-warning',
    LevelError: 'label-danger',
    LevelCritical: 'label-danger',
}

LevelBgClass = {
    LevelNotSet: 'bg-default',
    LevelDebug: 'bg-aqua',
    LevelInfo: 'bg-blue',
    LevelWarning: 'bg-orange',
    LevelError: 'bg-red',
    LevelCritical: 'bg-red',
}


# ################################################################################
# log entry directions

DirectionNone = 0
DirectionRequest = 1
DirectionResponse = 2
DirectionChoices = (
    (DirectionNone, "N/A"),
    (DirectionRequest, "REQ"),
    (DirectionResponse, "RSP"),
)
ValidDirections = [DirectionNone, DirectionRequest, DirectionResponse]

DirectionLabelClass = {
    DirectionNone: "label-default",
    DirectionRequest: "label-primary",
    DirectionResponse: "label-warning",
}

