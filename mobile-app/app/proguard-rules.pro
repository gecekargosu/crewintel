# Retrofit
-keepattributes Signature
-keepattributes Exceptions
-keep class com.crewintel.mobile.models.** { *; }
-keep class com.crewintel.mobile.api.** { *; }

# Gson
-keepattributes *Annotation*
-keep class sun.misc.Unsafe { *; }
-keep class com.google.gson.** { *; }

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
