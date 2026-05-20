/*
  SkyLight symbol-name constants for read-only inventory/probing.
  This file intentionally contains no callable function signatures.
  Treat names as hypotheses until verified on the target OS build.
*/
#pragma once

static const char * const SKYLIGHT_SYMBOL_NAMES[] = {
    "CGS",
    "CGSConnectionID",
    "CGSMainConnectionID",
    "CGSMoveWindowsToManagedSpace",
    "CGSRegisterConnectionNotifyProc",
    "CGSTickleActivityMonitor",
    "CGSize",
    "SLEventPostToPSN",
    "SLEventPostToPid",
    "SLEventRef",
    "SLEventSetAuthenticationMessage",
    "SLEventSetIntegerValueField",
    "SLPS",
    "SLPSPostEventRecordTo",
    "SLPSSetFrontProcessWithOptions",
    "SLSCopySpacesForWindows",
    "SLSEventAuthenticationMessage",
    "SLSEventRecord",
    "SLSGetActiveSpace",
    "SLSGetConnectionPSN",
    "SLSGetWindowOwner",
    "SLSHideSpaces",
    "SLSMainConnectionID",
    "SLSSetWindowAlpha",
    "SLSShowSpaces",
    "SLSSkyLightKeyEventAuthenticationMessage",
    "SLSSpaceAddWindowsAndRemoveFromSpaces",
    "SLSSpaceCreate",
    "SLSSpaceSetAbsoluteLevel",
    "SLSUpdateSystemActivityWithLocation",
    "_SLPSGetFrontProcess",
    0
};
