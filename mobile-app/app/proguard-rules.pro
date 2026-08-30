# CREWINTEL ProGuard Rules

# Keep Gson serialized models
-keepclassmembers class com.crewintel.mobile.models.** { *; }
-keep class com.crewintel.mobile.models.** { *; }

# Keep Retrofit API interfaces
-keep class com.crewintel.mobile.api.** { *; }
-keep interface com.crewintel.mobile.api.** { *; }

# Keep Gson annotations
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer

# Keep OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }

# Keep Retrofit
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }
-keepattributes Exceptions

# Keep Room/SQLite
-keep class org.sqlite.** { *; }
-keep class org.greenrobot.greendao.** { *; }

# Keep security-crypto
-keep class androidx.security.crypto.** { *; }

# Keep WorkManager
-keep class androidx.work.** { *; }

# Keep enum values
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# Keep Parcelable
-keep class * implements android.os.Parcelable {
    public static final android.os.Parcelable$Creator *;
}

# Suppress warnings for missing classes
-dontwarn javax.annotation.**
-dontwarn sun.misc.Unsafe
