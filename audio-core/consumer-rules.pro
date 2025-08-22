# This file contains ProGuard rules that will be applied to consumers of this
# library. ProGuard optimizations such as code shrinking and obfuscation are
# not available in this library project, so the rules here are focused on
# dead code elimination and code structure preservation.

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep JNI methods
-keep class com.audioplayerpro.audio.core.AudioPlayerNative {
    *;
}