# This file contains ProGuard rules that will be applied to consumers of this
# library. ProGuard optimizations such as code shrinking and obfuscation are
# not available in this library project, so the rules here are focused on
# dead code elimination and code structure preservation.

# Keep TensorFlow Lite classes
-keep class org.tensorflow.lite.** { *; }
-keep class org.tensorflow.lite.support.** { *; }

# Keep WorkManager classes
-keep class androidx.work.** { *; }

# Keep Room database classes
-keep class com.audioplayerpro.audio.ml.** { *; }