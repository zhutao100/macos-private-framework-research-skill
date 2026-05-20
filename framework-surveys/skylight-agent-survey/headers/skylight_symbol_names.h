/*
  SkyLight symbol-name constants for read-only inventory/probing.
  This file intentionally contains no callable function signatures.
  Treat names as hypotheses until verified on the target OS build.
*/
#pragma once

static const char * const SKYLIGHT_C_SYMBOL_NAMES[] = {
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
    "SLSEventRecord",
    "SLSGetActiveSpace",
    "SLSGetConnectionPSN",
    "SLSGetWindowOwner",
    "SLSHideSpaces",
    "SLSMainConnectionID",
    "SLSSetWindowAlpha",
    "SLSShowSpaces",
    "SLSSpaceAddWindowsAndRemoveFromSpaces",
    "SLSSpaceCreate",
    "SLSSpaceSetAbsoluteLevel",
    "SLSUpdateSystemActivityWithLocation",
    "_SLPSGetFrontProcess",
    0
};

static const char * const SKYLIGHT_OBJC_CLASS_NAMES[] = {
    "SLContentFilter",
    "SLContentStream",
    "SLSEventAuthenticationMessage",
    "SLSSkyLightEventAuthenticationMessage",
    "SLSSkyLightKeyEventAuthenticationMessage",
    "SLSBridgedCopyManagedDisplaySpacesOperation",
    "SLSBridgedCopySpacesForWindowsOperation",
    "SLSBridgedMoveWindowsToManagedSpaceOperation",
    "SLSBridgedSpaceSetAbsoluteLevelOperation",
    "SLWindowMirroringManager",
    0
};
